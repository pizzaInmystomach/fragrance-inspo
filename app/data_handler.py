from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import re
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "fragrance")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "perfume")


def _validate_uri(uri: str) -> bool:
    if not uri:
        raise ValueError("未設定 MONGO_URI。請檢查 .env 或系統環境變數。")
    if "<" in uri or ">" in uri:
        raise ValueError("MONGO_URI 含有佔位符 '<' 或 '>'，請移除並填入實際密碼。")
    return True


class DataHandler:
    """處理香水資料的類"""

    def __init__(self, uri=MONGO_URI, db_name=DB_NAME, collection_name=COLLECTION_NAME):
        try:
            _validate_uri(uri)
            # 設定短的 serverSelectionTimeoutMS 以便於快速失敗並回報錯誤
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            print(f"成功連線到MongoDB: {db_name}.{collection_name}")
        except Exception as e:
            print(f"MongoDB連線失敗: {e}")
            raise e

    def get_all_fragrances(self, limit=None):
        """獲取所有香水資料

        Args:
            limit (int, optional): 限制返回的數量，用於測試

        Returns:
            list: 香水資料列表
        """
        try:
            if limit:
                fragrances = list(self.collection.find().limit(limit))
            else:
                fragrances = list(self.collection.find())

            print(f"成功獲取 {len(fragrances)} 筆香水資料")
            return fragrances
        except Exception as e:
            print(f"獲取香水資料時發生錯誤: {e}")
            return []

    def get_fragrance_batches(self, batch_size=50, interval_seconds=1.0):
        """分批遍歷整個香水集合，每批之間暫停指定秒數。"""
        batch_size = max(1, int(batch_size))
        interval_seconds = max(0.0, float(interval_seconds))
        batches = []
        last_id = None
        batch_number = 0
        total_count = 0

        try:
            while True:
                query = {"_id": {"$gt": last_id}} if last_id is not None else {}
                batch = list(
                    self.collection.find(query)
                    .sort("_id", 1)
                    .limit(batch_size)
                )

                if not batch:
                    break

                batches.append(batch)
                batch_number += 1
                total_count += len(batch)
                last_id = batch[-1]["_id"]
                print(
                    f"MongoDB 批次 {batch_number}: 取得 {len(batch)} 筆，"
                    f"累計 {total_count} 筆"
                )

                if len(batch) < batch_size:
                    break

                if interval_seconds > 0:
                    time.sleep(interval_seconds)

            print(
                f"MongoDB 分批遍歷完成，共 {batch_number} 批、"
                f"{total_count} 筆香水資料"
            )
            return batches
        except Exception as e:
            print(f"分批獲取香水資料時發生錯誤: {e}")
            return []

    def get_relevant_fragrances(self, search_terms, limit=500):
        """依 accords/notes 搜尋相關香水，並補足到固定候選數。"""
        limit = max(1, int(limit))
        normalized_terms = []

        for term in search_terms:
            cleaned = str(term).strip().lower()
            if len(cleaned) >= 3 and cleaned not in normalized_terms:
                normalized_terms.append(cleaned)

        searchable_fields = [
            "Accords",
            "main_accords",
            "top_notes",
            "heart_notes",
            "base_notes",
            "Notes.Top Notes",
            "Notes.Middle Notes",
            "Notes.Heart Notes",
            "Notes.Base Notes",
        ]

        try:
            fragrances = []
            if normalized_terms:
                pattern = "|".join(re.escape(term) for term in normalized_terms)
                query = {
                    "$or": [
                        {field: {"$regex": pattern, "$options": "i"}}
                        for field in searchable_fields
                    ]
                }
                fragrances = list(self.collection.find(query).limit(limit))

            if len(fragrances) < limit:
                remaining = limit - len(fragrances)
                existing_ids = [fragrance["_id"] for fragrance in fragrances]
                fill_query = (
                    {"_id": {"$nin": existing_ids}}
                    if existing_ids
                    else {}
                )
                fragrances.extend(
                    list(self.collection.find(fill_query).limit(remaining))
                )

            print(
                f"MongoDB 情境檢索完成：關鍵詞 {normalized_terms}，"
                f"取得 {len(fragrances)} 筆候選"
            )
            return fragrances
        except Exception as e:
            print(f"情境檢索香水資料時發生錯誤: {e}")
            return []

    def get_fragrance_by_id(self, fragrance_id):
        """根據ID獲取香水

        Args:
            fragrance_id (str): 香水ID

        Returns:
            dict: 香水資料，如果未找到返回None
        """
        try:
            # 嘗試作為ObjectId查詢
            if isinstance(fragrance_id, str) and len(fragrance_id) == 24:
                fragrance = self.collection.find_one({"_id": ObjectId(fragrance_id)})
            else:
                # 嘗試作為字符串ID查詢
                fragrance = self.collection.find_one({"_id": fragrance_id})

            if fragrance:
                print(f"成功找到香水: {fragrance.get('Name', 'Unknown')}")
            else:
                print(f"未找到ID為 {fragrance_id} 的香水")

            return fragrance
        except Exception as e:
            print(f"查詢香水時發生錯誤: {e}")
            return None

    def get_fragrances_by_brand(self, brand_name):
        """根據品牌獲取香水

        Args:
            brand_name (str): 品牌名稱

        Returns:
            list: 該品牌的香水列表
        """
        try:
            # 使用正則表達式進行不區分大小寫的模糊搜索
            fragrances = list(
                self.collection.find({"Brand": {"$regex": brand_name, "$options": "i"}})
            )

            print(f"找到品牌 '{brand_name}' 的 {len(fragrances)} 筆香水")
            return fragrances
        except Exception as e:
            print(f"按品牌查詢時發生錯誤: {e}")
            return []

    def get_fragrances_by_accord(self, accord):
        """根據香調獲取香水

        Args:
            accord (str): 香調名稱

        Returns:
            list: 包含該香調的香水列表
        """
        try:
            fragrances = list(
                self.collection.find({"Accords": {"$regex": accord, "$options": "i"}})
            )

            print(f"找到含有香調 '{accord}' 的 {len(fragrances)} 筆香水")
            return fragrances
        except Exception as e:
            print(f"按香調查詢時發生錯誤: {e}")
            return []

    def test_connection(self):
        """測試資料庫連接和資料結構

        Returns:
            dict: 測試結果
        """
        try:
            # 測試連線
            self.client.admin.command("ping")

            # 獲取一筆資料來檢查結構
            sample = self.collection.find_one()

            if sample:
                print("資料庫連線成功！")
                print("範例資料結構:")
                for key, value in sample.items():
                    if key == "Notes" and isinstance(value, dict):
                        print(f"  {key}:")
                        for note_key, note_value in value.items():
                            print(f"    {note_key}: {note_value}")
                    else:
                        print(f"  {key}: {value}")

                return {
                    "success": True,
                    "sample_data": sample,
                    "total_count": self.collection.count_documents({}),
                }
            else:
                print("資料庫連線成功，但集合中沒有資料")
                return {"success": True, "sample_data": None, "total_count": 0}

        except Exception as e:
            print(f"資料庫連線測試失敗: {e}")
            return {"success": False, "error": str(e)}

    def close_connection(self):
        """關閉資料庫連線"""
        try:
            self.client.close()
            print("資料庫連線已關閉")
        except Exception as e:
            print(f"關閉連線時發生錯誤: {e}")


# 使用範例和測試函數
if __name__ == "__main__":
    # 測試資料處理器
    handler = DataHandler()

    # 測試連接
    test_result = handler.test_connection()

    if test_result["success"]:
        print(f"\n總共有 {test_result['total_count']} 筆香水資料")

        # 測試獲取少量資料
        fragrances = handler.get_all_fragrances(limit=3)

        if fragrances:
            print(f"\n前3筆香水資料:")
            for i, fragrance in enumerate(fragrances, 1):
                print(
                    f"{i}. {fragrance.get('Name', 'Unknown')} by {fragrance.get('Brand', 'Unknown')}"
                )

    # 關閉連線
    handler.close_connection()
