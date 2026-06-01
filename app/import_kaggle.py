import csv
import os
import ast
from pymongo import MongoClient, errors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_NAME = "fra_cleaned.csv"


def clean_notes(notes_raw):
    """將 Kaggle 裡的字串列表或逗號分隔文字轉成 Python list。"""
    if not notes_raw:
        return []

    notes_raw = str(notes_raw).strip()
    if notes_raw.startswith("[") and notes_raw.endswith("]"):
        try:
            return [str(item).strip() for item in ast.literal_eval(notes_raw)]
        except Exception:
            pass

    return [item.strip() for item in notes_raw.split(",") if item.strip()]


def parse_float(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def collect_main_accords(row):
    accords = []
    for index in range(1, 6):
        value = row.get(f"mainaccord{index}", "")
        if value:
            text = str(value).strip()
            if text:
                accords.append(text)
    return accords


def build_document(row):
    name = str(row.get("Perfume", "")).strip()
    brand = str(row.get("Brand", "")).strip()
    if not name or not brand:
        return None

    return {
        "url": str(row.get("url", "")).strip(),
        "name": name,
        "brand": brand,
        "country": str(row.get("Country", "")).strip(),
        "gender": str(row.get("Gender", "")).strip(),
        "rating_value": parse_float(row.get("Rating Value", "")),
        "rating_count": parse_int(row.get("Rating Count", "")),
        "year": parse_int(row.get("Year", "")),
        "top_notes": clean_notes(row.get("Top", "")),
        "middle_notes": clean_notes(row.get("Middle", "")),
        "base_notes": clean_notes(row.get("Base", "")),
        "perfumers": [
            perfumer.strip()
            for perfumer in [row.get("Perfumer1", ""), row.get("Perfumer2", "")]
            if perfumer and str(perfumer).strip()
        ],
        "main_accords": collect_main_accords(row),
    }


def import_csv_to_mongodb():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGO_DB_NAME", "fragrance")
    collection_name = os.getenv("MONGO_COLLECTION_NAME", "perfume")
    csv_name = os.getenv("KAGGLE_CSV_NAME", DEFAULT_CSV_NAME)
    csv_path = os.path.join(BASE_DIR, "data", csv_name)

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到 CSV 檔案，請確認路徑：{csv_path}")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db[collection_name]

        documents = []
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                doc = build_document(row)
                if doc:
                    documents.append(doc)

        if not documents:
            print("[系統訊息] 未找到可匯入的資料，請檢查 CSV 標頭與內容格式。")
            return

        print(f"[系統訊息] 準備寫入 {len(documents)} 筆資料到 {db_name}.{collection_name}...")
        result = collection.insert_many(documents, ordered=False)
        print(f"[系統訊息] 匯入完成：{len(result.inserted_ids)} 筆新資料。")

    except errors.ServerSelectionTimeoutError:
        print("[錯誤] 無法連線至 MongoDB，請確認 MongoDB 已啟動，且 MONGO_URI 正確。")
    except errors.BulkWriteError as bwe:
        print(f"[錯誤] 部分資料匯入失敗：{bwe.details}")
    except Exception as e:
        print(f"[錯誤] 匯入流程發生異常: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    import_csv_to_mongodb()
