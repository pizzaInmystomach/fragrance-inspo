from pydantic import BaseModel, Field
from typing import List, Optional

class FragranceSchema(BaseModel):
    id: str = Field(..., description="香水唯一識別碼")
    name: str = Field(..., description="香水名稱")
    brand: str = Field(..., description="香水品牌")
    top_notes: List[str] = Field(default_factory=list, description="前調")
    middle_notes: List[str] = Field(default_factory=list, description="中調")
    base_notes: List[str] = Field(default_factory=list, description="後調")
    main_accords: List[str] = Field(default_factory=list, description="主要香氣特徵")
    traits: List[str] = Field(default_factory=list, description="性格特徵標籤")
    style: List[str] = Field(default_factory=list, description="風格分類")
    seasonality: List[str] = Field(default_factory=list, description="季節適配性")
    occasions: List[str] = Field(default_factory=list, description="使用場合")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "f001",
                "name": "Tobacco Vanille",
                "brand": "Tom Ford",
                "top_notes": ["Tobacco Leaf", "Spices"],
                "middle_notes": ["Vanilla", "Cocoa", "Tobacco Flower"],
                "base_notes": ["Dried Fruits", "Woody Notes"],
                "main_accords": ["Oriental Spicy", "Warm", "Sweet"],
                "traits": ["Luxurious", "Confident", "Mature"],
                "style": ["High-end", "Classic"],
                "seasonality": ["Fall", "Winter"],
                "occasions": ["Evening Events", "Formal Occasions"]
            }
        }

    def to_embedding_text(self) -> str:
        """
        將所有欄位組合成完整文本描述，作為 Embedding 模型的輸入源。
        """
        notes_text = f"前調: {', '.join(self.top_notes)}。中調: {', '.join(self.middle_notes)}。後調: {', '.join(self.base_notes)}。"
        accords_text = f"香氣特徵: {', '.join(self.main_accords)}。" if self.main_accords else ""
        traits_text = f"性格: {', '.join(self.traits)}。" if self.traits else ""
        style_text = f"風格: {', '.join(self.style)}。" if self.style else ""
        season_text = f"季節: {', '.join(self.seasonality)}。" if self.seasonality else ""
        occasions_text = f"場合: {', '.join(self.occasions)}。" if self.occasions else ""
        
        return f"品牌: {self.brand}。名稱: {self.name}。{notes_text}{accords_text}{traits_text}{style_text}{season_text}{occasions_text}"