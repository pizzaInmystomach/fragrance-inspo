import os
import re
import json
import asyncio
import logging
from time import perf_counter_ns
import ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from app.search_engine import HybridSearchEngine

app = FastAPI(title="Local Fragrance Inspo Hybrid RAG API")

# 讀取環境變數，若不存在則預設連線本地端 (適用於非 Docker 環境測試)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_client = ollama.Client(host=OLLAMA_HOST)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化本地混合檢索引擎
try:
    engine = HybridSearchEngine()
except Exception as e:
    print(f"[警告] 檢索引擎初始化失敗，請確認階段三是否已成功生成資料庫：{e}")
    engine = None

# 定義 Pydantic 請求與回應規格
class RecommendRequest(BaseModel):
    user_prompt: str = Field(..., description="使用者的情境或香調期望描述")

class RecommendationItem(BaseModel):
    id: str
    name: str
    brand: str
    reason: str

class LatencyMetrics(BaseModel):
    embedding_latency_ms: float = Field(..., description="向量化延遲 (ms)")
    retrieval_latency_ms: float = Field(..., description="檢索與 RRF 融合延遲 (ms)")
    llm_generation_latency_ms: float = Field(..., description="LLM 文本生成延遲 (ms)")
    end_to_end_latency_ms: float = Field(..., description="總端到端延遲 (ms)")
    generation_throughput_tokens_sec: float = Field(..., description="詞生成速率 (Tokens/sec)")

class RecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]
    metrics: LatencyMetrics

class LLMRecommendationPayload(BaseModel):
    recommendations: List[RecommendationItem]

# 非同步包裝函數：將阻礙事件循環的同步 LanceDB 查詢放到獨立線程執行
def sanitize_fts_text(text: str) -> str:
    # Tantivy query parser 不接受某些特殊字元，先以空白替換這些符號
    cleaned = re.sub(r'["\'’‘“”–—\\/:@#^&*()\[\]{}<>!?|~$%+=,.]+', ' ', text)
    return re.sub(r"\s+", " ", cleaned).strip()

async def async_vector_search(table, vector, limit):
    return await asyncio.to_thread(
        lambda: table.search(vector, vector_column_name="embedding").limit(limit).to_list()
    )

async def async_fts_search(table, text, limit):
    safe_text = sanitize_fts_text(text)
    return await asyncio.to_thread(
        lambda: table.search(safe_text, fts_columns=["brand", "name", "bm25_text"]).limit(limit).to_list()
    )

@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend_fragrances(request: RecommendRequest):
    if engine is None or engine.table is None:
        raise HTTPException(status_code=500, detail="本地檢索資料庫未就緒，請先執行階段三。")
    
    # 啟動總端到端計時
    start_e2e = perf_counter_ns()
    
    try:
        # 1. 將使用者輸入轉為向量 (耗時約數十毫秒)
        start_emb = perf_counter_ns()
        emb_res = await asyncio.to_thread(
            ollama_client.embed,
            model="nomic-embed-text",
            input=request.user_prompt
        )
        end_emb = perf_counter_ns()
        embedding_latency = (end_emb - start_emb) / 1_000_000  # 轉為毫秒
        query_vector = emb_res.get("embeddings", [[]])[0]

        if not query_vector:
            raise HTTPException(status_code=500, detail="無法生成輸入文字的語意向量。")

        # 2. 實作作業系統任務平行化：同步觸發雙軌檢索，由耗時最長者決定回傳時間
        start_ret = perf_counter_ns()
        limit = 5
        task_vector = async_vector_search(engine.table, query_vector, limit * 2)
        task_fts = async_fts_search(engine.table, request.user_prompt, limit * 2)
        
        # 併發執行
        vector_results, fts_results = await asyncio.gather(task_vector, task_fts)

        # 3. 透過 RRF 演算法進行排序融合 (純數學運算，無 I/O 阻塞)
        retrieved_docs = engine._rrf(vector_results, fts_results, k=60)[:limit]
        end_ret = perf_counter_ns()
        retrieval_latency = (end_ret - start_ret) / 1_000_000  # 轉為毫秒

        if not retrieved_docs:
            raise HTTPException(status_code=404, detail="找不到任何相關的香水資料。")

        # 4. 拼接 Context 文本
        context_list = []
        for d in retrieved_docs:
            description = d.get("description") or d.get("metadata", {}).get("description", "")
            context_list.append(
                f"ID: {d['id']} | Brand: {d['brand']} | Name: {d['name']} | Description: {description}"
            )
        context_text = "\n---\n".join(context_list)

        # 5. 建置 Prompt 並嚴格要求 Llama 3 遵循 JSON 結構
        system_instruction = (
            "你是一個專業的香水推薦專家。請根據提供給你的『候選香水上下文資料』，"
            "從中篩選出最符合使用者期望的 3 款香水，並給出具體的推薦原因。\n"
            "關鍵規則：\n"
            "1. 只能從給定的上下文資料中進行選擇，不得虛構不存在的香水。\n"
            "2. 必須嚴格回傳合法的 JSON 格式，其結構必須包含一個 'recommendations' 陣列，"
            "陣列中的每個物件必須精確包含 'id', 'name', 'brand', 'reason' 四個鍵值。"
        )

        prompt = f"""
使用者期望的情境或感覺："{request.user_prompt}"

候選香水上下文資料：
{context_text}

請以規定的 JSON 格式回傳 3 款推薦香水。
"""

        # 6. 呼叫本地 Llama 3 生成推薦 (開啟 format='json' 啟用 JSON Mode)
        start_llm = perf_counter_ns()
        llm_response = await asyncio.to_thread(
            ollama_client.chat,
            model="llama3:8b",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            format="json"  # 強制 Ollama 底層約束 Token 輸出為 JSON
        )
        end_llm = perf_counter_ns()
        llm_latency = (end_llm - start_llm) / 1_000_000  # 轉為毫秒

        if isinstance(llm_response, dict):
            logger.info("llm_response keys: %s", list(llm_response.keys()))
            response_content = llm_response.get("message", {}).get("content")
            eval_count = llm_response.get('eval_count', 0)  # 生成的 Token 數量
        else:
            logger.info("llm_response type: %s", type(llm_response))
            logger.debug("llm_response full content: %s", llm_response)
            message_obj = getattr(llm_response, "message", None)
            response_content = getattr(message_obj, "content", None)
            eval_count = getattr(llm_response, 'eval_count', 0)
            
        # 計算詞生成速率 (Throughput) 與 總端到端延遲 (End-to-End Latency)
        llm_seconds = llm_latency / 1000.0
        generation_throughput = eval_count / llm_seconds if llm_seconds > 0 else 0.0
        
        end_e2e = perf_counter_ns()
        end_to_end_latency = (end_e2e - start_e2e) / 1_000_000

        if not response_content or not isinstance(response_content, str):
            logger.error("Invalid llm_response content: %s", llm_response)
            raise HTTPException(status_code=502, detail="本地大模型回傳格式異常。")

        # 7. 解析並透過 Pydantic 進行二次規格校驗
        try:
            response_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error("JSON decode failed for llm_response content: %s, error: %s", response_content, e)
            raise HTTPException(status_code=502, detail="本地大模型回傳的 JSON 格式損毀。")

        try:
            llm_payload = LLMRecommendationPayload(**response_data)
        except Exception as e:
            logger.error("LLM response validation failed: %s", e)
            raise HTTPException(status_code=502, detail="本地大模型回傳的推薦格式不正確。")
        
        # 組裝最終回傳結構，附帶指標數據
        metrics_data = LatencyMetrics(
            embedding_latency_ms=round(embedding_latency, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            llm_generation_latency_ms=round(llm_latency, 2),
            end_to_end_latency_ms=round(end_to_end_latency, 2),
            generation_throughput_tokens_sec=round(generation_throughput, 2)
        )
        
        return RecommendResponse(
            recommendations=llm_payload.recommendations,
            metrics=metrics_data
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="本地大模型回傳的 JSON 格式損毀。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"執行期錯誤: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)