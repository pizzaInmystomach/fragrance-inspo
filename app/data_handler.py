import json
import os

class DataHandler:
    """處理香水資料的類"""
    
    def __init__(self, fragrances_path="app/data/fragrances.json"):
        self.fragrances_path = fragrances_path
        self.fragrances = self._load_fragrances()
    
    def _load_fragrances(self):
        """讀取香水資料"""
        try:
            if os.path.exists(self.fragrances_path):
                with open(self.fragrances_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"香水資料檔案不存在: {self.fragrances_path}")
                return []
        except Exception as e:
            print(f"讀取香水資料出錯: {str(e)}")
            return []
    
    def get_all_fragrances(self):
        """獲取所有香水"""
        return self.fragrances
    
    def get_fragrance_by_id(self, fragrance_id):
        """根據ID獲取香水"""
        for fragrance in self.fragrances:
            if fragrance["id"] == fragrance_id:
                return fragrance
        return None