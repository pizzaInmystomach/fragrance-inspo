from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging
import json
import os
import time
from time import perf_counter_ns

from app.ai.analyzer import CharacterAnalyzer
from app.data_handler import DataHandler

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化應用
app = FastAPI(
    title="香氛靈感 API", 
    description="基於情境與環境分析的香水推薦API",
    version="2.0.0"
)

# 設定CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該設定具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局變數用於服務初始化
analyzer = None
data_handler = None

# 定義資料模型
class RecommendationRequest(BaseModel):
    user_input: str
    num_recommendations: Optional[int] = 3

# 新增：智能輸入解析請求模型
class SmartInputRequest(BaseModel):
    user_input: str
    num_recommendations: Optional[int] = 3

# 新增：輸入解析回應模型
class InputParsingResponse(BaseModel):
    status: str  # success, need_clarification, invalid
    scene_prompt: Optional[str] = None
    intent: str
    message: str

# 新增：通用香水推薦請求模型
class FragranceRecommendRequest(BaseModel):
    user_prompt: str
    num_recommendations: Optional[int] = 3

class HealthResponse(BaseModel):
    status: str
    message: str
    database_status: str
    total_fragrances: int

class LatencyMetrics(BaseModel):
    embedding_latency_ms: float
    retrieval_latency_ms: float
    llm_generation_latency_ms: float
    end_to_end_latency_ms: float
    generation_throughput_tokens_sec: float

def _metrics_path() -> str:
    return os.path.join(os.getcwd(), ".venv", "fragrance_metrics.json")

def _write_metrics(metrics: LatencyMetrics, prompt_text: Optional[str] = None, endpoint: Optional[str] = None):
    """Append one metrics entry to .venv/fragrance_metrics.json."""
    metrics_path = _metrics_path()

    try:
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = []
    except Exception:
        data = []

    entry = {
        "timestamp": time.time(),
        "prompt": prompt_text,
        "endpoint": endpoint,
        "metrics": metrics.model_dump() if hasattr(metrics, "model_dump") else metrics.dict()
    }
    data.append(entry)

    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

def _latency_ms(start_ns: int, end_ns: int) -> float:
    return (end_ns - start_ns) / 1_000_000

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化服務"""
    global analyzer, data_handler
    
    try:
        logger.info("正在初始化服務...")
        
        # 初始化資料處理器
        data_handler = DataHandler()
        test_result = data_handler.test_connection()
        
        if not test_result["success"]:
            logger.error(f"資料庫連線失敗: {test_result['error']}")
            raise Exception(f"資料庫連線失敗: {test_result['error']}")
        
        logger.info(f"資料庫連線成功，共有 {test_result['total_count']} 筆香水資料")
        
        # 初始化分析器
        analyzer = CharacterAnalyzer()
        logger.info("情境分析器初始化成功")
        
        logger.info("所有服務初始化完成")
        
    except Exception as e:
        logger.error(f"服務初始化失敗: {str(e)}")
        raise e

# 關閉事件
@app.on_event("shutdown")  
async def shutdown_event():
    """應用關閉時清理資源"""
    global data_handler
    
    try:
        if data_handler:
            data_handler.close_connection()
            logger.info("資料庫連線已關閉")
    except Exception as e:
        logger.error(f"關閉連線時發生錯誤: {str(e)}")

# API路由
@app.get("/")
def read_root():
    """根路徑"""
    return JSONResponse(
        content={"message": "歡迎使用香氛靈感 API v2.0 - 現已支援情境與環境分析！"}, 
        media_type="application/json; charset=utf-8"
    )

@app.get("/health", response_model=HealthResponse)
def health_check():
    """健康檢查端點"""
    try:
        if not data_handler:
            return HealthResponse(
                status="error",
                message="資料處理器未初始化",
                database_status="disconnected",
                total_fragrances=0
            )
        
        test_result = data_handler.test_connection()
        
        return HealthResponse(
            status="healthy" if test_result["success"] else "unhealthy",
            message="服務運行正常" if test_result["success"] else "資料庫連線異常",
            database_status="connected" if test_result["success"] else "disconnected",
            total_fragrances=test_result.get("total_count", 0)
        )
        
    except Exception as e:
        return HealthResponse(
            status="error",
            message=f"健康檢查失敗: {str(e)}",
            database_status="unknown",
            total_fragrances=0
        )

# 新增：智能輸入解析端點
@app.post("/api/parse-input", response_model=InputParsingResponse)
def parse_user_input(request: SmartInputRequest):
    """
    解析用戶的自然語言情境/環境輸入
    支持各種表達方式：
    - "雨天圖書館"
    - "A woody fragrance with earth and old book pages"
    - "Something cozy for reading in the library on a rainy day"
    """
    try:
        # 檢查服務是否已初始化
        if not analyzer:
            raise HTTPException(
                status_code=503, 
                detail="服務尚未初始化完成，請稍後再試"
            )
        
        logger.info(f"解析用戶輸入: {request.user_input}")
        
        result = analyzer.parse_user_input(request.user_input.strip())
        
        if not result:
            return InputParsingResponse(
                status="invalid",
                scene_prompt=None,
                intent="Parse failed",
                message="I couldn't understand your request. Please describe a scene, environment, mood, or scent notes."
            )
        
        return InputParsingResponse(
            status=result.get("status", "invalid"),
            scene_prompt=result.get("scene_prompt"),
            intent=result.get("intent", ""),
            message=result.get("message", "")
        )
        
    except Exception as e:
        logger.error(f"輸入解析錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Input parsing failed: {str(e)}")

# 新增：智能香水推薦端點（完整流程）
@app.post("/api/recommend-smart")
def get_smart_recommendations(request: SmartInputRequest):
    """
    智能香水推薦 - 從情境/環境自然語言輸入開始到完整推薦
    """
    try:
        start_e2e = perf_counter_ns()

        # 檢查服務是否已初始化
        if not analyzer or not data_handler:
            raise HTTPException(
                status_code=503, 
                detail="服務尚未初始化完成，請稍後再試"
            )
        
        logger.info(f"開始智能推薦流程，用戶輸入: {request.user_input}")
        
        # 第1步：解析用戶輸入
        start_embedding = perf_counter_ns()
        parse_result = analyzer.parse_user_input(request.user_input.strip())
        
        if not parse_result:
            return JSONResponse(
                content={
                    "success": False,
                    "scene_prompt": None,
                    "scene_analysis": None,
                    "recommendations": [],
                    "message": "I couldn't understand your request. Please describe a scene, environment, mood, or scent notes.",
                    "error": "Input parsing failed"
                },
                media_type="application/json; charset=utf-8"
            )
        
        # 如果需要澄清或輸入無效，返回相應訊息
        if parse_result.get("status") != "success":
            return JSONResponse(
                content={
                    "success": False,
                    "scene_prompt": parse_result.get("scene_prompt"),
                    "scene_analysis": None,
                    "recommendations": [],
                    "message": parse_result.get("message", "Please provide more information."),
                    "error": None
                },
                media_type="application/json; charset=utf-8"
            )
        
        scene_prompt = parse_result.get("scene_prompt") or request.user_input.strip()
        
        logger.info(f"成功識別情境提示: {scene_prompt}")
        
        # 第2步：分析情境
        scene_analysis = analyzer.analyze_scene(scene_prompt)
        end_embedding = perf_counter_ns()
        embedding_latency = _latency_ms(start_embedding, end_embedding)
        
        # 第3步：獲取香水資料
        start_retrieval = perf_counter_ns()
        fragrances = data_handler.get_all_fragrances(limit=20)  # 限制數量以提高速度
        end_retrieval = perf_counter_ns()
        retrieval_latency = _latency_ms(start_retrieval, end_retrieval)
        
        if not fragrances:
            return JSONResponse(
                content={
                    "success": False,
                    "scene_prompt": scene_prompt,
                    "scene_analysis": scene_analysis,
                    "recommendations": [],
                    "message": "No fragrances found in database.",
                    "error": "Empty database"
                },
                media_type="application/json; charset=utf-8"
            )
        
        logger.info(f"獲取到 {len(fragrances)} 個香水進行匹配")
        
        # 第4步：匹配香水
        start_llm = perf_counter_ns()
        analyzer.reset_generation_metrics()
        match_result = analyzer.match_fragrances(
            scene_analysis, 
            fragrances, 
            request.num_recommendations
        )
        
        recommendations = []
        if match_result and match_result.get("recommendations"):
            for rec in match_result["recommendations"]:
                fragrance = rec["fragrance"]
                description = analyzer.generate_description(fragrance)
                
                recommendations.append({
                    "rank": rec["rank"],
                    "fragrance": {
                        "id": fragrance.get("id"),
                        "name": fragrance.get("Name"),
                        "brand": fragrance.get("Brand"),
                        "accords": fragrance.get("Accords", []),
                        "top_notes": fragrance.get("top_notes", []),
                        "heart_notes": fragrance.get("heart_notes", []),
                        "base_notes": fragrance.get("base_notes", []),
                        "additional_traits": fragrance.get("additional_traits", []),
                        "personality_match": fragrance.get("personality_match", []),
                        "mood_description": fragrance.get("mood_description", ""),
                        "season_suitability": fragrance.get("season_suitability", []),
                        "time_of_day": fragrance.get("time_of_day", [])
                    },
                    "rationale": rec["rationale"],
                    "description": description,
                    "match_score": rec.get("match_score", 0)
                })
        end_llm = perf_counter_ns()
        llm_latency = _latency_ms(start_llm, end_llm)
        llm_seconds = llm_latency / 1000.0
        eval_count = getattr(analyzer, "last_generation_tokens", 0)
        generation_throughput = eval_count / llm_seconds if llm_seconds > 0 else 0.0
        end_to_end_latency = _latency_ms(start_e2e, perf_counter_ns())

        metrics_data = LatencyMetrics(
            embedding_latency_ms=round(embedding_latency, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            llm_generation_latency_ms=round(llm_latency, 2),
            end_to_end_latency_ms=round(end_to_end_latency, 2),
            generation_throughput_tokens_sec=round(generation_throughput, 2)
        )

        try:
            _write_metrics(metrics_data, request.user_input, "/api/recommend-smart")
        except Exception:
            logger.exception("Failed to write metrics")
        
        success_message = f"Found {len(recommendations)} fragrance matches for this scene!"
        
        result = {
            "success": True,
            "scene_prompt": scene_prompt,
            "scene_analysis": scene_analysis,
            "recommendations": recommendations,
            "message": success_message,
            "error": None
        }
        
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        logger.error(f"智能推薦錯誤: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "scene_prompt": None,
                "scene_analysis": None,
                "recommendations": [],
                "message": "An error occurred while processing your request.",
                "error": str(e)
            },
            media_type="application/json; charset=utf-8"
        )

@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest):
    """根據情境與環境分析獲取香水推薦"""
    try:
        start_e2e = perf_counter_ns()

        # 檢查服務是否已初始化
        if not analyzer or not data_handler:
            raise HTTPException(
                status_code=503, 
                detail="服務尚未初始化完成，請稍後再試"
            )
        
        scene_prompt = request.user_input.strip()
        if not scene_prompt:
            raise HTTPException(status_code=400, detail="user_input 不可為空")

        logger.info(f"開始處理情境推薦請求: {scene_prompt}")
        
        # 1. 分析情境 (使用同步版本)
        start_embedding = perf_counter_ns()
        scene_analysis = analyzer.analyze_scene(scene_prompt)
        end_embedding = perf_counter_ns()
        embedding_latency = _latency_ms(start_embedding, end_embedding)
        logger.info(f"情境分析完成: {scene_prompt}")
        
        # 2. 獲取香水資料
        start_retrieval = perf_counter_ns()
        fragrances = data_handler.get_all_fragrances(limit=20)
        end_retrieval = perf_counter_ns()
        retrieval_latency = _latency_ms(start_retrieval, end_retrieval)
        if not fragrances:
            raise HTTPException(status_code=500, detail="無法獲取香水資料")
        
        logger.info(f"已獲取 {len(fragrances)} 筆香水資料")
        
        # 3. 匹配香水 (使用同步版本，取得3個推薦)
        start_llm = perf_counter_ns()
        analyzer.reset_generation_metrics()
        match_result = analyzer.match_fragrances(
            scene_analysis,
            fragrances,
            num_recommendations=request.num_recommendations
        )
        
        if not match_result or not match_result.get("recommendations"):
            raise HTTPException(status_code=404, detail="找不到合適的香水推薦")
        
        recommendations = match_result["recommendations"]
        logger.info(f"香水匹配完成，共 {len(recommendations)} 個推薦")
        
        # 4. 為每個推薦的香水生成描述
        enhanced_recommendations = []
        for rec in recommendations:
            fragrance = rec["fragrance"]
            description = analyzer.generate_description(fragrance)
            
            enhanced_rec = {
                "rank": rec["rank"],
                "fragrance": {
                    "id": fragrance.get("id"),
                    "name": fragrance.get("Name"),
                    "brand": fragrance.get("Brand"),
                    "accords": fragrance.get("Accords", []),
                    "top_notes": fragrance.get("top_notes", []),
                    "heart_notes": fragrance.get("heart_notes", []),
                    "base_notes": fragrance.get("base_notes", []),
                    "additional_traits": fragrance.get("additional_traits", []),
                    "personality_match": fragrance.get("personality_match", []),
                    "mood_description": fragrance.get("mood_description", ""),
                    "season_suitability": fragrance.get("season_suitability", []),
                    "time_of_day": fragrance.get("time_of_day", [])
                },
                "rationale": rec["rationale"],
                "description": description,
                "match_score": rec.get("match_score", 0)
            }
            enhanced_recommendations.append(enhanced_rec)
        end_llm = perf_counter_ns()
        llm_latency = _latency_ms(start_llm, end_llm)
        llm_seconds = llm_latency / 1000.0
        eval_count = getattr(analyzer, "last_generation_tokens", 0)
        generation_throughput = eval_count / llm_seconds if llm_seconds > 0 else 0.0
        end_to_end_latency = _latency_ms(start_e2e, perf_counter_ns())

        metrics_data = LatencyMetrics(
            embedding_latency_ms=round(embedding_latency, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            llm_generation_latency_ms=round(llm_latency, 2),
            end_to_end_latency_ms=round(end_to_end_latency, 2),
            generation_throughput_tokens_sec=round(generation_throughput, 2)
        )

        try:
            _write_metrics(
                metrics_data,
                scene_prompt,
                "/api/recommendations"
            )
        except Exception:
            logger.exception("Failed to write metrics")
        
        logger.info("所有香水描述生成完成")
        
        # 5. 組合推薦結果
        result = {
            "scene": {
                "prompt": scene_prompt,
                **scene_analysis
            },
            "recommendations": enhanced_recommendations,
            "total_recommendations": len(enhanced_recommendations),
            "timestamp": None  # 可以加入時間戳記
        }
        
        logger.info(f"推薦請求處理完成: {scene_prompt}")
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    
    except HTTPException:
        # 重新拋出 HTTPException
        raise
    except Exception as e:
        logger.error(f"處理推薦請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理推薦請求時出錯: {str(e)}")

@app.get("/metrics/latest")
def get_latest_metrics():
    """回傳 .venv/fragrance_metrics.json 中最新的一筆 metrics。"""
    metrics_path = _metrics_path()
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="No metrics found")

    try:
        with open(metrics_path, "r", encoding="utf-8") as fh:
            entries = json.load(fh)

        if not entries:
            raise HTTPException(status_code=404, detail="No metrics entries")

        return entries[-1]
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Metrics file corrupted")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error reading metrics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to read metrics")

# 新增：獲取熱門角色列表
@app.get("/api/characters/popular")
def get_popular_characters():
    """獲取熱門角色列表，幫助用戶選擇"""
    popular_characters = [
        {"name": "Harry Potter", "source": "Harry Potter", "description": "Brave, loyal, determined wizard"},
        {"name": "Hermione Granger", "source": "Harry Potter", "description": "Intelligent, studious, resourceful witch"},
        {"name": "Daisy Buchanan", "source": "The Great Gatsby", "description": "Elegant, sophisticated, mysterious socialite"},
        {"name": "James Bond", "source": "James Bond", "description": "Sophisticated, confident, suave secret agent"},
        {"name": "Audrey Hepburn", "source": "Classic Hollywood", "description": "Elegant, graceful, timeless icon"},
        {"name": "Jay Gatsby", "source": "The Great Gatsby", "description": "Romantic, ambitious, mysterious millionaire"},
    ]
    
    return JSONResponse(
        content={
            "popular_characters": popular_characters,
            "message": "You can ask for recommendations like: 'I want to smell like Harry Potter' or just 'Hermione Granger'"
        },
        media_type="application/json; charset=utf-8"
    )

@app.get("/api/fragrances")
def get_all_fragrances(limit: Optional[int] = None):
    """獲取所有香水資料"""
    try:
        if not data_handler:
            raise HTTPException(status_code=503, detail="資料處理器尚未初始化")
        
        fragrances = data_handler.get_all_fragrances(limit=limit)
        
        # 格式化回傳資料
        formatted_fragrances = []
        for fragrance in fragrances:
            notes_obj = fragrance.get('Notes', {})
            formatted_fragrance = {
                "id": str(fragrance.get('_id')),
                "name": fragrance.get('Name', '').replace(',', '').strip(),
                "brand": fragrance.get('Brand', '').replace(',', '').strip(),
                "accords": fragrance.get('Accords', '').replace(',', ', ').strip().split(', ') if fragrance.get('Accords') else [],
                "notes": {
                    "top": notes_obj.get('Top Notes', '').replace(',', ', ').strip(),
                    "heart": notes_obj.get('Heart Notes', '').replace(',', ', ').strip(),
                    "base": notes_obj.get('Base Notes', '').replace(',', ', ').strip()
                }
            }
            formatted_fragrances.append(formatted_fragrance)
        
        return JSONResponse(
            content={
                "total": len(formatted_fragrances),
                "fragrances": formatted_fragrances
            },
            media_type="application/json; charset=utf-8"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取香水資料時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取香水資料時出錯: {str(e)}")

@app.get("/api/fragrances/{fragrance_id}")
def get_fragrance_by_id(fragrance_id: str):
    """根據ID獲取特定香水資料"""
    try:
        if not data_handler:
            raise HTTPException(status_code=503, detail="資料處理器尚未初始化")
        
        fragrance = data_handler.get_fragrance_by_id(fragrance_id)
        
        if not fragrance:
            raise HTTPException(status_code=404, detail="找不到指定的香水")
        
        # 使用分析器增強資料
        if analyzer:
            enhanced_fragrance = analyzer.enhance_fragrance_data(fragrance)
            return JSONResponse(
                content=enhanced_fragrance,
                media_type="application/json; charset=utf-8"
            )
        else:
            # 如果分析器未初始化，返回基本資料
            notes_obj = fragrance.get('Notes', {})
            basic_fragrance = {
                "id": str(fragrance.get('_id')),
                "name": fragrance.get('Name', '').replace(',', '').strip(),
                "brand": fragrance.get('Brand', '').replace(',', '').strip(),
                "accords": fragrance.get('Accords', '').replace(',', ', ').strip().split(', ') if fragrance.get('Accords') else [],
                "notes": {
                    "top": notes_obj.get('Top Notes', '').replace(',', ', ').strip(),
                    "heart": notes_obj.get('Heart Notes', '').replace(',', ', ').strip(),
                    "base": notes_obj.get('Base Notes', '').replace(',', ', ').strip()
                }
            }
            return JSONResponse(
                content=basic_fragrance,
                media_type="application/json; charset=utf-8"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取香水資料時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取香水資料時出錯: {str(e)}")

# 僅在直接執行此檔案時啟動服務器
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
