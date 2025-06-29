from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


class DataHandler:
    """處理香水資料的類"""

    def __init__(self, uri=MONGO_URI, db_name="fragrance", collection_name="perfume"):
        try:
            self.client = MongoClient(uri)
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
