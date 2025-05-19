from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from app.ai.analyzer import CharacterAnalyzer
from app.data_handler import DataHandler

# 初始化應用
app = FastAPI(title="香氛靈感 API", description="基於角色分析的香水推薦API")

# 初始化服務
analyzer = CharacterAnalyzer()
data_handler = DataHandler()

# 定義資料模型
class RecommendationRequest(BaseModel):
    character_name: str
    source_type: Optional[str] = ""

# API路由
@app.get("/")
def read_root():
    return {"message": "歡迎使用香氛靈感 API"}

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """獲取角色香水推薦"""
    try:
        # 1. 分析角色
        character_analysis = await analyzer.analyze_character(
            request.character_name, 
            request.source_type
        )
        
        # 2. 獲取香水資料
        fragrances = data_handler.get_all_fragrances()
        if not fragrances:
            raise HTTPException(status_code=500, detail="無法獲取香水資料")
        
        # 3. 匹配香水
        match_result = await analyzer.match_fragrance(
            character_analysis,
            fragrances
        )
        
        # 4. 生成香水描述
        description = await analyzer.generate_description(match_result["fragrance"])
        
        # 5. 組合推薦結果
        result = {
            "character": {
                "name": request.character_name,
                "source": request.source_type,
                **character_analysis
            },
            "fragrance": match_result["fragrance"],
            "rationale": match_result["rationale"],
            "description": description
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理推薦請求時出錯: {str(e)}")

# 僅在直接執行此檔案時啟動服務器
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)