import os
from dotenv import load_dotenv
# 載入環境變數
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
print(f"MongoDB URI: {MONGO_URI}")
from pymongo import MongoClient

uri = MONGO_URI
client = MongoClient(uri)

try:
    db_names = client.list_database_names()
    print("連線成功，資料庫清單：", db_names)
except Exception as e:
    print("連線失敗：", e)