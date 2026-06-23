import os
import re
import json
import asyncio
import logging
import time
import uuid
import subprocess
import resource
from time import perf_counter_ns
from datetime import datetime
import ollama
from fastapi import FastAPI, HTTPException
from typing import Any, Dict, List, Optional
from app.api.schemas import LLMRecommendationPayload, RecommendRequest
from app.search_engine import HybridSearchEngine
from app.retrieval.retrieve import retrieve

try:
    import psutil
except ImportError:
    psutil = None

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

def _current_branch() -> str:
    configured_branch = os.getenv("METRICS_BRANCH")
    if configured_branch:
        return configured_branch
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=os.getcwd(),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"

def _metrics_path(branch: str) -> str:
    configured_path = os.getenv("METRICS_PATH")
    if configured_path:
        return configured_path
    branch_group = re.sub(r"[^A-Za-z0-9._-]+", "-", branch.split("/", 1)[0])
    return os.path.join(
        os.getcwd(), "metrics", f"fragrance_request_metrics-{branch_group}.jsonl"
    )

def _result_ids(results: List[dict]) -> List[str]:
    return [str(result["id"]) for result in results if result.get("id") is not None]

class ResourceSampler:
    def __init__(self, interval_seconds: float = 0.05):
        self.interval_seconds = interval_seconds
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self.swap_peak_mb = 0.0
        self._stopped = asyncio.Event()
        self._task = None
        self._started_at = time.perf_counter()
        self._cpu_started_at = time.process_time()

    async def start(self):
        self._task = asyncio.create_task(self._sample())

    async def stop(self) -> dict:
        if self._task is not None and not self._stopped.is_set():
            self._stopped.set()
            await self._task

        if self.memory_samples:
            memory_avg = sum(self.memory_samples) / len(self.memory_samples)
            memory_peak = max(self.memory_samples)
        else:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            memory_peak = float(usage.ru_maxrss)
            if os.uname().sysname == "Darwin":
                memory_peak /= 1024 ** 2
            else:
                memory_peak /= 1024
            memory_avg = memory_peak

        if self.cpu_samples:
            cpu_avg = sum(self.cpu_samples) / len(self.cpu_samples)
            cpu_peak = max(self.cpu_samples)
        else:
            elapsed = max(time.perf_counter() - self._started_at, 1e-9)
            cpu_avg = 100 * (time.process_time() - self._cpu_started_at) / elapsed
            cpu_peak = cpu_avg

        return {
            "memory_avg_mb": round(memory_avg, 2),
            "memory_peak_mb": round(memory_peak, 2),
            "cpu_avg_percent": round(cpu_avg, 2),
            "cpu_peak_percent": round(cpu_peak, 2),
            "swap_mb": round(self.swap_peak_mb, 2),
        }

    async def _sample(self):
        if psutil is None:
            return

        process = psutil.Process()
        process.cpu_percent(interval=None)
        while not self._stopped.is_set():
            try:
                self.memory_samples.append(process.memory_info().rss / 1024 ** 2)
                self.cpu_samples.append(process.cpu_percent(interval=None))
                self.swap_peak_mb = max(
                    self.swap_peak_mb, psutil.swap_memory().used / 1024 ** 2
                )
            except (psutil.Error, OSError):
                logger.exception("Failed to sample process resources")
                return
            try:
                await asyncio.wait_for(
                    self._stopped.wait(), timeout=self.interval_seconds
                )
            except asyncio.TimeoutError:
                pass

# 非同步包裝函數：將阻礙事件循環的同步 LanceDB 查詢放到獨立線程執行
def sanitize_fts_text(text: str) -> str:
    # Tantivy query parser 不接受某些特殊字元，先以空白替換這些符號
    cleaned = re.sub(r'["\'’‘“”–—\\/:@#^&*()\[\]{}<>!?|~$%+=,.]+', ' ', text)
    return re.sub(r"\s+", " ", cleaned).strip()

async def async_vector_search(table, vector, limit):
    started_at = perf_counter_ns()
    results = await asyncio.to_thread(
        lambda: table.search(vector, vector_column_name="embedding").limit(limit).to_list()
    )
    return results, (perf_counter_ns() - started_at) / 1_000_000

async def async_fts_search(table, text, limit):
    safe_text = sanitize_fts_text(text)
    started_at = perf_counter_ns()
    results = await asyncio.to_thread(
        lambda: table.search(safe_text, fts_columns=["brand", "name", "bm25_text"]).limit(limit).to_list()
    )
    return results, (perf_counter_ns() - started_at) / 1_000_000

VALID_LLM_MODES = {"cloud", "local", "none"}
VALID_BENCHMARK_MODES = {"retrieval_only", "e2e"}


def _normalise_mode(name: str, value: str, valid_modes: set[str]) -> str:
    value = value.strip().lower()
    if value not in valid_modes:
        raise ValueError(
            f"Unknown {name}={value!r}. Expected one of: "
            f"{', '.join(sorted(valid_modes))}."
        )
    return value


def _mode_from_request_or_env(
    name: str,
    request_value: Optional[str],
    default: str,
    valid_modes: set[str],
) -> str:
    return _normalise_mode(
        name,
        request_value if request_value is not None else os.getenv(name, default),
        valid_modes,
    )


def _experiment_config(request: RecommendRequest) -> dict:
    benchmark_mode = _mode_from_request_or_env(
        "BENCHMARK_MODE",
        request.benchmark_mode,
        "e2e",
        VALID_BENCHMARK_MODES,
    )
    llm_mode = _mode_from_request_or_env(
        "LLM_MODE",
        request.llm_mode,
        "local",
        VALID_LLM_MODES,
    )
    if benchmark_mode == "retrieval_only":
        llm_mode = "none"
    return {
        "retriever_mode": _mode_from_request_or_env(
            "RETRIEVER_MODE",
            request.retriever_mode,
            "hybrid",
            {"baseline", "hybrid"},
        ),
        "llm_mode": llm_mode,
        "benchmark_mode": benchmark_mode,
    }


def _empty_metrics() -> Dict[str, Any]:
    return {
        "end_to_end_ms": None,
        "embedding_ms": None,
        "baseline_ms": None,
        "bm25_ms": None,
        "hnsw_ms": None,
        "rrf_ms": None,
        "retrieval_total_ms": None,
        "llm_generation_ms": None,
        "input_tokens": None,
        "output_tokens": None,
        "tokens_per_sec": None,
        "estimated_embedding_cost_saved_usd": 0,
        "estimated_llm_generation_cost_saved_usd": 0,
        "estimated_cost_saved_per_1000_queries_usd": 0,
    }


def _retrieval_debug(retrieval_result: dict, final_ids: Optional[List[str]] = None) -> dict:
    debug = retrieval_result.get("debug") or {}
    return {
        "retrieved_ids": retrieval_result.get("retrievedIds", []),
        "baseline_top_ids": debug.get("baseline_top_ids", []),
        "bm25_top_ids": debug.get("bm25_top_ids", []),
        "hnsw_top_ids": debug.get("hnsw_top_ids", []),
        "rrf_top_ids": debug.get("rrf_top_ids", []),
        "final_recommendation_ids": final_ids or [],
    }


def _context_text(results: List[dict]) -> str:
    context = []
    for item in results:
        description = item.get("description", "")
        context.append(
            "ID: {id} | Brand: {brand} | Name: {name} | Accords: {accords} | "
            "Top: {top} | Middle: {middle} | Base: {base} | Description: {description}".format(
                id=item.get("id", ""),
                brand=item.get("brand", ""),
                name=item.get("name", ""),
                accords=", ".join(item.get("accords") or []),
                top=", ".join(item.get("top_notes") or []),
                middle=", ".join(item.get("middle_notes") or []),
                base=", ".join(item.get("base_notes") or []),
                description=description,
            )
        )
    return "\n---\n".join(context)


def _generation_messages(query_text: str, retrieved_docs: List[dict]) -> List[dict]:
    system_instruction = (
        "You are a professional fragrance recommendation expert. Select exactly "
        "3 fragrances from the candidate context. Do not invent fragrances. "
        "Return only valid JSON with a recommendations array. Each object must "
        "have string fields id, name, brand, and reason."
    )
    prompt = f"""
User scent brief: "{query_text}"

Candidate fragrance context:
{_context_text(retrieved_docs)}

Return exactly 3 recommendations from these candidates.
"""
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
    ]


def _extract_json_object(text: str) -> dict:
    if not text:
        raise ValueError("empty LLM response")
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])

    if isinstance(parsed, list):
        return {"recommendations": parsed}
    if not isinstance(parsed, dict):
        raise ValueError(f"LLM response JSON must be an object, got {type(parsed).__name__}.")
    return parsed


def _validate_llm_payload(response_content: str, candidate_ids: set[str]) -> LLMRecommendationPayload:
    response_data = _extract_json_object(response_content)
    candidate_payload = LLMRecommendationPayload(**response_data)
    recommendation_ids = [
        recommendation.id for recommendation in candidate_payload.recommendations
    ]
    invalid_ids = set(recommendation_ids) - candidate_ids
    if invalid_ids:
        raise ValueError(
            f"recommendation IDs outside retrieved candidates: {sorted(invalid_ids)}"
        )
    if len(set(recommendation_ids)) != len(recommendation_ids):
        raise ValueError("duplicate recommendation IDs")
    return candidate_payload


def _tokens_per_sec(output_tokens: int, duration_ns: int, fallback_ms: float) -> float:
    seconds = duration_ns / 1_000_000_000 if duration_ns else fallback_ms / 1000.0
    return output_tokens / seconds if seconds > 0 else 0.0


async def _generate_local_recommendations(query_text: str, retrieved_docs: List[dict]) -> dict:
    started_at = perf_counter_ns()
    max_attempts = max(1, int(os.getenv("LLM_MAX_ATTEMPTS", "3")))
    candidate_ids = set(_result_ids(retrieved_docs))
    messages = _generation_messages(query_text, retrieved_docs)
    llm_payload = None
    input_tokens = 0
    output_tokens = 0
    eval_duration = 0
    last_validation_error = None

    for attempt in range(1, max_attempts + 1):
        llm_response = await asyncio.to_thread(
            ollama_client.chat,
            model=os.getenv("OLLAMA_LLM_MODEL", "llama3:8b"),
            messages=messages,
            format=LLMRecommendationPayload.model_json_schema(),
            options={"temperature": 0},
        )
        if isinstance(llm_response, dict):
            response_content = llm_response.get("message", {}).get("content")
            input_tokens += int(llm_response.get("prompt_eval_count", 0) or 0)
            output_tokens += int(llm_response.get("eval_count", 0) or 0)
            eval_duration += int(llm_response.get("eval_duration", 0) or 0)
        else:
            message_obj = getattr(llm_response, "message", None)
            response_content = getattr(message_obj, "content", None)
            input_tokens += int(getattr(llm_response, "prompt_eval_count", 0) or 0)
            output_tokens += int(getattr(llm_response, "eval_count", 0) or 0)
            eval_duration += int(getattr(llm_response, "eval_duration", 0) or 0)

        try:
            llm_payload = _validate_llm_payload(response_content or "", candidate_ids)
            break
        except Exception as error:
            last_validation_error = error

        logger.warning(
            "Local LLM validation failed on attempt %s/%s: %s",
            attempt,
            max_attempts,
            last_validation_error,
        )
        if attempt < max_attempts:
            messages.extend(
                [
                    {"role": "assistant", "content": response_content or ""},
                    {
                        "role": "user",
                        "content": (
                            "The previous response was invalid. Return exactly 3 "
                            "complete recommendation objects with ids copied from "
                            "the candidate context."
                        ),
                    },
                ]
            )

    llm_ms = (perf_counter_ns() - started_at) / 1_000_000
    if llm_payload is None:
        raise HTTPException(
            status_code=502,
            detail=f"Local LLM returned invalid recommendations: {last_validation_error}",
        )
    return {
        "payload": llm_payload,
        "metrics": {
            "llm_generation_ms": round(llm_ms, 2),
            "llm_attempts": attempt,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tokens_per_sec": round(
                _tokens_per_sec(output_tokens, eval_duration, llm_ms), 2
            ),
        },
    }


def _extract_langchain_output_tokens(result) -> int:
    usage = getattr(result, "usage_metadata", None)
    if isinstance(usage, dict):
        for key in ("output_tokens", "completion_tokens"):
            if isinstance(usage.get(key), int):
                return usage[key]

    metadata = getattr(result, "response_metadata", None)
    if isinstance(metadata, dict):
        token_usage = metadata.get("token_usage", {})
        if isinstance(token_usage, dict):
            for key in ("completion_tokens", "output_tokens", "generated_tokens"):
                if isinstance(token_usage.get(key), int):
                    return token_usage[key]
    return 0


def _extract_langchain_input_tokens(result) -> int:
    usage = getattr(result, "usage_metadata", None)
    if isinstance(usage, dict):
        for key in ("input_tokens", "prompt_tokens"):
            if isinstance(usage.get(key), int):
                return usage[key]

    metadata = getattr(result, "response_metadata", None)
    if isinstance(metadata, dict):
        token_usage = metadata.get("token_usage", {})
        if isinstance(token_usage, dict):
            for key in ("prompt_tokens", "input_tokens"):
                if isinstance(token_usage.get(key), int):
                    return token_usage[key]
    return 0


async def _generate_cloud_recommendations(query_text: str, retrieved_docs: List[dict]) -> dict:
    started_at = perf_counter_ns()
    candidate_ids = set(_result_ids(retrieved_docs))
    max_attempts = max(
        2,
        int(os.getenv("CLOUD_LLM_MAX_ATTEMPTS", os.getenv("LLM_MAX_ATTEMPTS", "2"))),
    )
    messages = _generation_messages(query_text, retrieved_docs)
    llm_payload = None
    input_tokens = 0
    output_tokens = 0
    last_validation_error = None

    def _invoke_cloud(messages_to_send: List[dict]):
        from app.ai.llm_config import get_balanced_model

        llm = get_balanced_model()
        return llm.invoke(messages_to_send)

    for attempt in range(1, max_attempts + 1):
        result = await asyncio.to_thread(_invoke_cloud, messages)
        input_tokens += _extract_langchain_input_tokens(result)
        output_tokens += _extract_langchain_output_tokens(result)
        content = result.content if hasattr(result, "content") else str(result)
        try:
            llm_payload = _validate_llm_payload(content, candidate_ids)
            break
        except Exception as error:
            last_validation_error = error

        logger.warning(
            "Cloud LLM validation failed on attempt %s/%s: %s",
            attempt,
            max_attempts,
            last_validation_error,
        )
        if attempt < max_attempts:
            messages.extend(
                [
                    {"role": "assistant", "content": content or ""},
                    {
                        "role": "user",
                        "content": (
                            "The previous response was invalid. Return one JSON "
                            "object with a recommendations array containing exactly "
                            "3 complete objects. Do not return a bare array."
                        ),
                    },
                ]
            )

    llm_ms = (perf_counter_ns() - started_at) / 1_000_000
    if llm_payload is None:
        raise HTTPException(
            status_code=502,
            detail=f"Cloud LLM returned invalid recommendations: {last_validation_error}",
        )
    return {
        "payload": llm_payload,
        "metrics": {
            "llm_generation_ms": round(llm_ms, 2),
            "llm_attempts": attempt,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tokens_per_sec": round(
                output_tokens / (llm_ms / 1000.0) if llm_ms > 0 else 0.0,
                2,
            ),
        },
    }


async def _generate_recommendations(llm_mode: str, query_text: str, retrieved_docs: List[dict]) -> dict:
    if llm_mode == "none":
        return {"payload": None, "metrics": {}}
    if llm_mode == "local":
        return await _generate_local_recommendations(query_text, retrieved_docs)
    if llm_mode == "cloud":
        return await _generate_cloud_recommendations(query_text, retrieved_docs)
    raise ValueError(f"Unknown LLM_MODE={llm_mode!r}.")


def _estimated_cost_metrics(metrics: dict, llm_mode: str) -> dict:
    input_rate = float(os.getenv("CLOUD_INPUT_COST_PER_1M_TOKENS", "0.05"))
    output_rate = float(os.getenv("CLOUD_OUTPUT_COST_PER_1M_TOKENS", "0.08"))
    estimated_cloud_cost = (
        (metrics.get("input_tokens") or 0) * input_rate
        + (metrics.get("output_tokens") or 0) * output_rate
    ) / 1_000_000
    saved = 0.0 if llm_mode == "cloud" else estimated_cloud_cost
    return {
        "estimated_embedding_cost_saved_usd": 0,
        "estimated_llm_generation_cost_saved_usd": round(saved, 8),
        "estimated_cost_saved_per_1000_queries_usd": round(saved * 1000, 6),
    }


def _metric_present(metrics: dict, key: str) -> bool:
    value = metrics.get(key)
    return value is not None and value != 0


def _validate_benchmark_state(
    experiment_config: dict,
    metrics: dict,
    retrieval_debug: dict,
    generation_result: dict,
) -> None:
    if experiment_config["benchmark_mode"] == "retrieval_only":
        llm_metrics = (
            "llm_generation_ms",
            "input_tokens",
            "output_tokens",
            "tokens_per_sec",
            "llm_attempts",
        )
        if generation_result.get("payload") is not None or any(
            _metric_present(metrics, key) for key in llm_metrics
        ):
            raise RuntimeError(
                "Invalid benchmark state: retrieval_only mode called LLM generation."
            )

    if experiment_config["retriever_mode"] == "baseline":
        hybrid_metrics_exist = any(
            _metric_present(metrics, key)
            for key in ("embedding_ms", "bm25_ms", "hnsw_ms", "rrf_ms")
        )
        hybrid_debug_exists = any(
            retrieval_debug.get(key)
            for key in ("bm25_top_ids", "hnsw_top_ids", "rrf_top_ids")
        )
        if hybrid_metrics_exist or hybrid_debug_exists:
            raise RuntimeError(
                "Invalid benchmark state: baseline mode produced hybrid metrics."
            )

    if experiment_config["retriever_mode"] == "hybrid":
        if _metric_present(metrics, "baseline_ms") or retrieval_debug.get(
            "baseline_top_ids"
        ):
            raise RuntimeError(
                "Invalid benchmark state: hybrid mode produced baseline metrics."
            )

@app.post("/api/recommend")
async def recommend_fragrances(request: RecommendRequest):
    query_text = request.query_text()
    if not query_text:
        raise HTTPException(
            status_code=422, detail="Either prompt or user_prompt is required."
        )

    # 啟動總端到端計時
    start_e2e = perf_counter_ns()
    request_id = str(uuid.uuid4())
    branch = request.branch or _current_branch()
    sampler = ResourceSampler()
    await sampler.start()
    
    try:
        experiment_config = _experiment_config(request)
        if experiment_config["retriever_mode"] == "hybrid" and (
            engine is None or engine.table is None
        ):
            raise HTTPException(status_code=500, detail="本地檢索資料庫未就緒，請先執行階段三。")

        retrieval_result = await retrieve(
            query=query_text,
            top_k=request.top_k,
            mode=experiment_config["retriever_mode"],
            engine=engine,
            ollama_client=ollama_client,
        )
        retrieved_docs = retrieval_result.get("results", [])
        if not retrieved_docs:
            raise HTTPException(status_code=404, detail="找不到任何相關的香水資料。")

        generation_result = await _generate_recommendations(
            experiment_config["llm_mode"],
            query_text,
            retrieved_docs,
        )
        llm_payload = generation_result.get("payload")
        recommendations = (
            [
                recommendation.model_dump()
                if hasattr(recommendation, "model_dump")
                else recommendation.dict()
                for recommendation in llm_payload.recommendations
            ]
            if llm_payload is not None
            else []
        )
        final_recommendation_ids = [
            recommendation["id"] for recommendation in recommendations
        ]

        resource_metrics = await sampler.stop()
        end_to_end_latency = (perf_counter_ns() - start_e2e) / 1_000_000
        metrics = _empty_metrics()
        metrics.update(retrieval_result.get("metrics") or {})
        metrics.update(generation_result.get("metrics") or {})
        metrics["end_to_end_ms"] = round(end_to_end_latency, 2)
        metrics.update(
            _estimated_cost_metrics(metrics, experiment_config["llm_mode"])
        )

        retrieval_debug = _retrieval_debug(
            retrieval_result,
            final_ids=final_recommendation_ids,
        )
        _validate_benchmark_state(
            experiment_config,
            metrics,
            retrieval_debug,
            generation_result,
        )
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        response = {
            "request_id": request_id,
            "timestamp": timestamp,
            "query_id": request.query_id,
            "query": query_text,
            "query_type": request.query_type,
            "run_index": request.run_index,
            "cache_state": request.cache_state,
            "branch": branch,
            "experiment_config": experiment_config,
            "metrics": {
                **metrics,
                **resource_metrics,
            },
            "retrieval_debug": retrieval_debug,
            "recommendations": recommendations,
        }
        return response

        # 1. 將使用者輸入轉為向量 (耗時約數十毫秒)
        start_emb = perf_counter_ns()
        emb_res = await asyncio.to_thread(
            ollama_client.embed,
            model="nomic-embed-text",
            input=query_text
        )
        end_emb = perf_counter_ns()
        embedding_latency = (end_emb - start_emb) / 1_000_000  # 轉為毫秒
        query_vector = emb_res.get("embeddings", [[]])[0]

        if not query_vector:
            raise HTTPException(status_code=500, detail="無法生成輸入文字的語意向量。")

        # 2. 實作作業系統任務平行化：同步觸發雙軌檢索，由耗時最長者決定回傳時間
        start_ret = perf_counter_ns()
        limit = request.top_k
        task_vector = async_vector_search(engine.table, query_vector, limit * 2)
        task_fts = async_fts_search(engine.table, query_text, limit * 2)
        
        # 併發執行
        vector_search, fts_search = await asyncio.gather(task_vector, task_fts)
        vector_results, hnsw_latency = vector_search
        fts_results, bm25_latency = fts_search

        # 3. 透過 RRF 演算法進行排序融合 (純數學運算，無 I/O 阻塞)
        start_rrf = perf_counter_ns()
        retrieved_docs = engine._rrf(vector_results, fts_results, k=60)[:limit]
        rrf_latency = (perf_counter_ns() - start_rrf) / 1_000_000
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
使用者期望的情境或感覺："{query_text}"

候選香水上下文資料：
{context_text}

請以規定的 JSON 格式回傳 3 款推薦香水。
"""

        # 6. 呼叫本地 Llama 3，並在格式或候選 ID 不合法時自動重試。
        start_llm = perf_counter_ns()
        max_llm_attempts = max(1, int(os.getenv("LLM_MAX_ATTEMPTS", "3")))
        candidate_ids = set(_result_ids(retrieved_docs))
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]
        llm_payload = None
        prompt_eval_count = 0
        eval_count = 0
        eval_duration = 0
        last_validation_error = None

        for attempt in range(1, max_llm_attempts + 1):
            llm_response = await asyncio.to_thread(
                ollama_client.chat,
                model="llama3:8b",
                messages=messages,
                format=LLMRecommendationPayload.model_json_schema(),
                options={"temperature": 0},
            )

            if isinstance(llm_response, dict):
                logger.info("llm_response keys: %s", list(llm_response.keys()))
                response_content = llm_response.get("message", {}).get("content")
                attempt_eval_count = llm_response.get("eval_count", 0)
                attempt_prompt_count = llm_response.get("prompt_eval_count", 0)
                attempt_eval_duration = llm_response.get("eval_duration", 0)
            else:
                logger.info("llm_response type: %s", type(llm_response))
                logger.debug("llm_response full content: %s", llm_response)
                message_obj = getattr(llm_response, "message", None)
                response_content = getattr(message_obj, "content", None)
                attempt_eval_count = getattr(llm_response, "eval_count", 0)
                attempt_prompt_count = getattr(
                    llm_response, "prompt_eval_count", 0
                )
                attempt_eval_duration = getattr(
                    llm_response, "eval_duration", 0
                )

            eval_count += int(attempt_eval_count or 0)
            prompt_eval_count += int(attempt_prompt_count or 0)
            eval_duration += int(attempt_eval_duration or 0)

            try:
                if not response_content or not isinstance(response_content, str):
                    raise ValueError("empty or non-string response content")

                response_data = json.loads(response_content)
                candidate_payload = LLMRecommendationPayload(**response_data)
                recommendation_ids = [
                    recommendation.id
                    for recommendation in candidate_payload.recommendations
                ]
                invalid_ids = set(recommendation_ids) - candidate_ids
                if invalid_ids:
                    raise ValueError(
                        f"recommendation IDs outside retrieved candidates: "
                        f"{sorted(invalid_ids)}"
                    )
                if len(set(recommendation_ids)) != len(recommendation_ids):
                    raise ValueError("duplicate recommendation IDs")

                llm_payload = candidate_payload
                break
            except (json.JSONDecodeError, ValueError, TypeError) as error:
                last_validation_error = error
            except Exception as error:
                last_validation_error = error

            logger.warning(
                "LLM response validation failed on attempt %s/%s: %s",
                attempt,
                max_llm_attempts,
                last_validation_error,
            )
            if attempt < max_llm_attempts:
                messages.extend(
                    [
                        {
                            "role": "assistant",
                            "content": response_content or "",
                        },
                        {
                            "role": "user",
                            "content": (
                                "The previous response was invalid. Return exactly "
                                "3 complete recommendation objects. Every id must be "
                                "copied exactly from the candidate context, and every "
                                "object must contain string fields id, name, brand, "
                                "and reason. Do not use booleans or null values."
                            ),
                        },
                    ]
                )

        end_llm = perf_counter_ns()
        llm_latency = (end_llm - start_llm) / 1_000_000  # 轉為毫秒

        # 計算詞生成速率 (Throughput) 與 總端到端延遲 (End-to-End Latency)
        llm_seconds = (
            eval_duration / 1_000_000_000
            if eval_duration
            else llm_latency / 1000.0
        )
        generation_throughput = eval_count / llm_seconds if llm_seconds > 0 else 0.0

        if llm_payload is None:
            logger.error(
                "LLM response remained invalid after %s attempts: %s",
                max_llm_attempts,
                last_validation_error,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "本地大模型多次回傳不合法的推薦格式；"
                    "請重試此 benchmark query。"
                ),
            )

        resource_metrics = await sampler.stop()
        end_to_end_latency = (perf_counter_ns() - start_e2e) / 1_000_000
        metrics_entry = {
            "branch": branch,
            "request_id": request_id,
            "query": query_text,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "end_to_end_ms": round(end_to_end_latency, 2),
            "embedding_ms": round(embedding_latency, 2),
            "bm25_ms": round(bm25_latency, 2),
            "hnsw_ms": round(hnsw_latency, 2),
            "rrf_ms": round(rrf_latency, 2),
            "retrieval_total_ms": round(retrieval_latency, 2),
            "llm_generation_ms": round(llm_latency, 2),
            "llm_attempts": attempt,
            "input_tokens": int(prompt_eval_count or 0),
            "output_tokens": int(eval_count or 0),
            "tokens_per_sec": round(generation_throughput, 2),
            "retrieved_ids": _result_ids(retrieved_docs),
            "bm25_top_ids": _result_ids(fts_results),
            "hnsw_top_ids": _result_ids(vector_results),
            "rrf_top_ids": _result_ids(retrieved_docs),
            "final_recommendation_ids": [
                recommendation.id for recommendation in llm_payload.recommendations
            ],
            **resource_metrics,
        }
        if request.query_id:
            metrics_entry["query_id"] = request.query_id
        if request.query_type:
            metrics_entry["query_type"] = request.query_type
        if request.run_index is not None:
            metrics_entry["run_index"] = request.run_index

        if request.return_metrics or request.return_retrieval_debug:
            response = {
                "request_id": request_id,
                "timestamp": metrics_entry["timestamp"],
                "recommendations": [
                    recommendation.model_dump()
                    if hasattr(recommendation, "model_dump")
                    else recommendation.dict()
                    for recommendation in llm_payload.recommendations
                ],
            }
            if request.return_metrics:
                response["metrics"] = {
                    key: value
                    for key, value in metrics_entry.items()
                    if key
                    in {
                        "end_to_end_ms",
                        "embedding_ms",
                        "bm25_ms",
                        "hnsw_ms",
                        "rrf_ms",
                        "retrieval_total_ms",
                        "llm_generation_ms",
                        "llm_attempts",
                        "input_tokens",
                        "output_tokens",
                        "tokens_per_sec",
                        "memory_avg_mb",
                        "memory_peak_mb",
                        "cpu_avg_percent",
                        "cpu_peak_percent",
                        "swap_mb",
                    }
                }
            if request.return_retrieval_debug:
                response["retrieval_debug"] = {
                    "retrieved_ids": metrics_entry["retrieved_ids"],
                    "bm25_top_ids": metrics_entry["bm25_top_ids"],
                    "hnsw_top_ids": metrics_entry["hnsw_top_ids"],
                    "rrf_top_ids": metrics_entry["rrf_top_ids"],
                    "final_recommendation_ids": metrics_entry[
                        "final_recommendation_ids"
                    ],
                }
            return response

        metrics_path = _metrics_path(branch)

        def _append_metrics():
            os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
            with open(metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(metrics_entry, ensure_ascii=False) + "\n")

        await asyncio.to_thread(_append_metrics)

        return llm_payload.recommendations
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="本地大模型回傳的 JSON 格式損毀。")
    except Exception as e:
        logger.exception("Recommendation request %s failed", request_id)
        raise HTTPException(status_code=500, detail=f"執行期錯誤: {str(e)}")
    finally:
        await sampler.stop()


@app.get("/metrics/latest")
async def get_latest_metrics():
    """回傳目前 branch JSONL metrics 中最新的一筆。"""
    metrics_path = _metrics_path(_current_branch())
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="No metrics found")

    try:
        def _read():
            with open(metrics_path, "r", encoding="utf-8") as fh:
                lines = [line.strip() for line in fh if line.strip()]
            return json.loads(lines[-1]) if lines else None

        latest = await asyncio.to_thread(_read)
        if latest is None:
            raise HTTPException(status_code=404, detail="No metrics entries")
        return latest
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Metrics file corrupted")
    except Exception as e:
        logger.exception("Error reading metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to read metrics")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.server:app", host="127.0.0.1", port=8000, reload=True)
