from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_prompt: Optional[str] = Field(
        default=None, description="一般 API 使用的香水需求描述"
    )
    prompt: Optional[str] = Field(
        default=None, description="Benchmark 使用的香水需求描述"
    )
    query_id: Optional[str] = None
    query_type: Optional[str] = None
    branch: Optional[str] = None
    run_index: Optional[int] = Field(default=None, ge=1)
    cache_state: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=50)
    return_metrics: bool = False
    return_retrieval_debug: bool = False
    retriever_mode: Optional[str] = None
    llm_mode: Optional[str] = None
    benchmark_mode: Optional[str] = None

    def query_text(self) -> str:
        return (self.prompt or self.user_prompt or "").strip()


class RecommendationItem(BaseModel):
    id: str
    name: str
    brand: str
    reason: str


class LLMRecommendationPayload(BaseModel):
    recommendations: List[RecommendationItem] = Field(min_length=3, max_length=3)
