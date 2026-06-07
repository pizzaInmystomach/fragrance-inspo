import os
from dotenv import load_dotenv
# 載入環境變數
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
def _mask_uri(uri: str) -> str:
    if not uri:
        return "<empty>"
    # 嘗試遮罩密碼（若有）
    try:
        prefix, rest = uri.split("//", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            if ":" in creds:
                user, pwd = creds.split(":", 1)
                return f"{prefix}//{user}:<redacted>@{host}"
    except Exception:
        pass
    return uri


def _validate_uri(uri: str) -> bool:
    if not uri:
        print("[錯誤] 未在環境變數中設定 MONGO_URI。請檢查 .env 或系統環境變數。")
        return False
    if "<" in uri or ">" in uri:
        print("[錯誤] MONGO_URI 含有佔位符 '<' 或 '>'，請移除並填入實際密碼。")
        print("範例：mongodb+srv://user:password@cluster0.example.mongodb.net/mydb?retryWrites=true&w=majority")
        return False
    return True


print(f"MongoDB URI: {_mask_uri(MONGO_URI)}")

from pymongo import MongoClient

if not _validate_uri(MONGO_URI):
    raise SystemExit(1)

uri = MONGO_URI
client = MongoClient(uri, serverSelectionTimeoutMS=5000)

try:
    db_names = client.list_database_names()
    print("連線成功，資料庫清單：", db_names)
except Exception as e:
    print("連線失敗：", e)