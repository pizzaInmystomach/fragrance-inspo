import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 載入環境變數
load_dotenv(PROJECT_ROOT / ".env")

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
