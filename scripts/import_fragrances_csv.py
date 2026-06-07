import argparse
import csv
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "fragrance")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "perfume")


def normalize_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if item and item.strip()]
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items


def parse_number(value):
    if not value:
        return None
    try:
        value = value.replace(" ", "").replace(",", ".")
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def build_document(row):
    accords = [row.get(f"mainaccord{i}", "").strip() for i in range(1, 6)]
    accords = [item for item in accords if item]

    top_notes = normalize_list(row.get("Top"))
    middle_notes = normalize_list(row.get("Middle"))
    base_notes = normalize_list(row.get("Base"))

    return {
        "url": row.get("url", "").strip(),
        "Name": row.get("Perfume", "").strip(),
        "Brand": row.get("Brand", "").strip(),
        "Country": row.get("Country", "").strip(),
        "Gender": row.get("Gender", "").strip(),
        "Rating Value": parse_number(row.get("Rating Value")),
        "Rating Count": parse_number(row.get("Rating Count")),
        "Year": parse_number(row.get("Year")),
        "Notes": {
            "Top Notes": row.get("Top", "").strip(),
            "Middle Notes": row.get("Middle", "").strip(),
            "Base Notes": row.get("Base", "").strip(),
        },
        "top_notes": top_notes,
        "heart_notes": middle_notes,
        "base_notes": base_notes,
        "Perfumer1": row.get("Perfumer1", "").strip(),
        "Perfumer2": row.get("Perfumer2", "").strip(),
        "Accords": accords,
        "main_accords": accords,
    }


def import_csv(file_path, uri, db_name, collection_name, drop=False):
    if not uri:
        raise ValueError("MONGO_URI is required. Set it in the environment or pass --uri.")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    collection = db[collection_name]

    if drop:
        collection.delete_many({})
        print(f"已清空集合 {db_name}.{collection_name}")

    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        docs = [build_document(row) for row in reader if row.get("Perfume")]

    if not docs:
        print("未找到可匯入的資料。請檢查 CSV 是否正確。")
        return

    result = collection.insert_many(docs)
    print(f"已匯入 {len(result.inserted_ids)} 筆資料到 {db_name}.{collection_name}")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="匯入香水CSV資料到 MongoDB")
    parser.add_argument("--file", default="app/data/fra_cleaned.csv", help="CSV 檔案路徑")
    parser.add_argument("--uri", default=MONGO_URI, help="MongoDB 連線字串")
    parser.add_argument("--db", default=DB_NAME, help="資料庫名稱")
    parser.add_argument("--collection", default=COLLECTION_NAME, help="集合名稱")
    parser.add_argument("--drop", action="store_true", help="先清空集合再匯入")
    args = parser.parse_args()

    import_csv(args.file, args.uri, args.db, args.collection, drop=args.drop)


if __name__ == "__main__":
    main()
