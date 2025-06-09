from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging

from app.ai.analyzer import CharacterAnalyzer
from app.data_handler import DataHandler

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化應用
app = FastAPI(
    title="香氛靈感 API", 
    description="基於角色分析的香水推薦API",
    version="1.0.0"
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
    character_name: str
    source_type: Optional[str] = ""

class HealthResponse(BaseModel):
    status: str
    message: str
    database_status: str
    total_fragrances: int

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
        logger.info("角色分析器初始化成功")
        
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
        content={"message": "歡迎使用香氛靈感 API"}, 
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

@app.post("/api/recommendations")
def get_recommendations(request: RecommendationRequest):
    """獲取角色香水推薦"""
    try:
        # 檢查服務是否已初始化
        if not analyzer or not data_handler:
            raise HTTPException(
                status_code=503, 
                detail="服務尚未初始化完成，請稍後再試"
            )
        
        logger.info(f"開始處理推薦請求: {request.character_name}")
        
        # 1. 分析角色 (使用同步版本)
        character_analysis = analyzer.analyze_character(
            request.character_name, 
            request.source_type
        )
        logger.info(f"角色分析完成: {request.character_name}")
        
        # 2. 獲取香水資料
        fragrances = data_handler.get_all_fragrances()
        if not fragrances:
            raise HTTPException(status_code=500, detail="無法獲取香水資料")
        
        logger.info(f"已獲取 {len(fragrances)} 筆香水資料")
        
        # 3. 匹配香水 (使用同步版本，取得3個推薦)
        match_result = analyzer.match_fragrances(
            character_analysis,
            fragrances,
            num_recommendations=3
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
        
        logger.info("所有香水描述生成完成")
        
        # 5. 組合推薦結果
        result = {
            "character": {
                "name": request.character_name,
                "source": request.source_type,
                **character_analysis
            },
            "recommendations": enhanced_recommendations,
            "total_recommendations": len(enhanced_recommendations),
            "timestamp": None  # 可以加入時間戳記
        }
        
        logger.info(f"推薦請求處理完成: {request.character_name}")
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    
    except HTTPException:
        # 重新拋出 HTTPException
        raise
    except Exception as e:
        logger.error(f"處理推薦請求時出錯: {str(e)}")
        raise HTTPException(status_code=500, detail=f"處理推薦請求時出錯: {str(e)}")

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