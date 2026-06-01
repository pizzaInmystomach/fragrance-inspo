import re
from pydantic import BaseModel, Field, validator
from typing import List, Optional


class KaggleFragranceSchema(BaseModel):
    id: str  # 自行生成的唯一識別碼
    url: Optional[str] = ""
    brand: str
    name: str
    country: Optional[str] = ""
    gender: Optional[str] = ""
    rating_value: Optional[float] = None
    rating_count: Optional[int] = None
    year: Optional[int] = None
    perfumer1: Optional[str] = ""
    perfumer2: Optional[str] = ""
    description: Optional[str] = ""
    accords: List[str] = Field(default_factory=list)  # 新增：香調輪廓對於 Hybrid Search 至關重要
    top_notes: List[str] = Field(default_factory=list)
    middle_notes: List[str] = Field(default_factory=list, alias="heart_notes") # 增加別名以相容不同命名
    # `box_notes` historically used in data; expose as alias but prefer `base_notes`
    base_notes: List[str] = Field(default_factory=list, alias="box_notes")
    # Optional dense vector (填入時應為 384 或 768 維)
    embedding: Optional[List[float]] = None

    def to_bm25_text(self) -> str:
        """回傳單段純文字，適合送入 BM25 分詞/索引或檢視。"""
        notes = " ".join(self.top_notes + self.middle_notes + self.base_notes)
        accords_str = " ".join(self.accords)
        parts = [self.brand, self.name, accords_str, notes, self.description or ""]
        return " ".join([p for p in parts if p]).lower()

    def to_bm25_tokens(self) -> List[str]:
        """將 `to_bm25_text()` 做簡單清理與 tokenization，回傳可用於稀疏索引的 tokens。"""
        text = self.to_bm25_text()
        # 移除非字母數字字元，保留空格
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return [t for t in text.split() if len(t) > 1]

    def to_embedding_text(self) -> str:
        """組合成適合本地 Embedding 模型的純文字段落。"""
        accords_str = f"Accords: {', '.join(self.accords)}." if self.accords else ""
        notes_str = f"Top: {', '.join(self.top_notes)}. Middle: {', '.join(self.middle_notes)}. Base: {', '.join(self.base_notes)}."
        return f"Brand: {self.brand} | Name: {self.name} | {accords_str} | Notes: {notes_str} | Description: {self.description or ''}"

    def to_lancedb_doc(self) -> dict:
        """回傳一個 dict，方便直接上傳到 LanceDB 或其他向量/稀疏混合索引。

        結構範例：{
            "id": str,
            "bm25_text": str,
            "bm25_tokens": List[str],  # optional
            "embedding": Optional[List[float]],
            "metadata": { ... }
        }
        """
        return {
            "id": self.id,
            "url": self.url,
            "brand": self.brand,
            "name": self.name,
            "bm25_text": self.to_bm25_text(),
            "bm25_tokens": self.to_bm25_tokens(),
            "embedding": self.embedding,
            "metadata": {
                "url": self.url,
                "brand": self.brand,
                "name": self.name,
                "country": self.country,
                "gender": self.gender,
                "rating_value": self.rating_value,
                "rating_count": self.rating_count,
                "year": self.year,
                "perfumer1": self.perfumer1,
                "perfumer2": self.perfumer2,
                "description": self.description,
                "accords": self.accords,
                "top_notes": self.top_notes,
                "middle_notes": self.middle_notes,
                "base_notes": self.base_notes,
            },
        }

    @validator("id")
    def id_must_not_be_empty(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("id must not be empty")
        return v2

    class Config:
        # Pydantic V2 note: 'allow_population_by_field_name' was renamed.
        # Use 'validate_by_name' to preserve population by field name behavior in V2.
        validate_by_name = True