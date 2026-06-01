import os
import csv
import time
import chromadb
from google import genai
from google.genai.errors import ClientError
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", os.getenv("KAGGLE_CSV_NAME", "fra_cleaned.csv"))
CSV_ENCODING = os.getenv("KAGGLE_CSV_ENCODING", "latin-1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_REQUEST_INTERVAL = float(os.getenv("EMBEDDING_REQUEST_INTERVAL", "2.0"))


def clean_notes(notes_raw):
    if not notes_raw:
        return []
    notes_text = str(notes_raw).strip()
    return [item.strip() for item in notes_text.split(",") if item.strip()]


def build_embedding_text(row: dict) -> str:
    top_notes = clean_notes(row.get("Top", ""))
    middle_notes = clean_notes(row.get("Middle", ""))
    base_notes = clean_notes(row.get("Base", ""))

    parts = [
        f"品牌: {row.get('Brand', '').strip()}",
        f"名稱: {row.get('Perfume', '').strip()}"
    ]

    if top_notes:
        parts.append(f"前調: {', '.join(top_notes)}")
    if middle_notes:
        parts.append(f"中調: {', '.join(middle_notes)}")
    if base_notes:
        parts.append(f"後調: {', '.join(base_notes)}")

    main_accords = [
        str(row.get(f"mainaccord{i}", "")).strip()
        for i in range(1, 6)
        if str(row.get(f"mainaccord{i}", "")).strip()
    ]
    if main_accords:
        parts.append(f"香氣特徵: {', '.join(main_accords)}")

    return "。".join(parts)


def format_metadata(row: dict) -> dict:
    return {
        "url": row.get("url", "").strip(),
        "name": row.get("Perfume", "").strip(),
        "brand": row.get("Brand", "").strip(),
        "country": row.get("Country", "").strip(),
        "gender": row.get("Gender", "").strip(),
        "rating_value": row.get("Rating Value", "").strip(),
        "rating_count": row.get("Rating Count", "").strip(),
        "year": row.get("Year", "").strip(),
        "top_notes": ", ".join(clean_notes(row.get("Top", ""))),
        "middle_notes": ", ".join(clean_notes(row.get("Middle", ""))),
        "base_notes": ", ".join(clean_notes(row.get("Base", ""))),
        "perfumers": ", ".join(
            [p.strip() for p in [row.get("Perfumer1", ""), row.get("Perfumer2", "")] if p and str(p).strip()]
        ),
        "main_accords": ", ".join(
            [str(row.get(f"mainaccord{i}", "")).strip() for i in range(1, 6) if str(row.get(f"mainaccord{i}", "")).strip()]
        )
    }


def chunk_list(items, chunk_size=100):
    for start in range(0, len(items), chunk_size):
        yield items[start:start + chunk_size]


def run_ingestion():
    """執行 Kaggle CSV 讀取並寫入本地 ChromaDB。"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：環境變數中缺少 GEMINI_API_KEY，請先配置該變數。")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"錯誤：找不到 Kaggle CSV 檔案，路徑應為：{CSV_PATH}")

    ai_client = genai.Client(api_key=api_key)

    rows = []
    with open(CSV_PATH, "r", encoding=CSV_ENCODING) as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if not row.get("Perfume") or not row.get("Brand"):
                continue
            rows.append(row)

    if not rows:
        print("[錯誤] CSV 讀取後沒有有效資料。請確認 CSV 正確使用分號分隔，且包含 Perfume 和 Brand 欄位。")
        return

    texts_to_embed = [build_embedding_text(row) for row in rows]
    print(f"[向量化進行中] 開始呼叫 Google GenAI 替 {len(texts_to_embed)} 筆香水文本生成語意向量...")

    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def embed_batch_with_retry(batch):
        return ai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch
        )

    generated_embeddings = []
    try:
        for batch_index, batch in enumerate(chunk_list(texts_to_embed, 100), start=1):
            print(f"[向量化批次] 正在處理第 {batch_index} 批，共 {len(batch)} 筆...")
            response = embed_batch_with_retry(batch)
            if not response.embeddings or len(response.embeddings) != len(batch):
                raise RuntimeError(
                    f"向量模型返回異常：期望 {len(batch)} 個向量，實際得到 {len(response.embeddings) if response.embeddings else 0} 個。"
                )
            generated_embeddings.extend([emb.values for emb in response.embeddings])
            time.sleep(EMBEDDING_REQUEST_INTERVAL)

        print(f"[成功] 已生成 {len(generated_embeddings)} 個向量。向量維度: {len(generated_embeddings[0]) if generated_embeddings else 0}")
    except Exception as e:
        raise RuntimeError(f"呼叫 Gemini Embedding API 失敗: {str(e)}")

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, (row, vector) in enumerate(zip(rows, generated_embeddings), start=1):
        doc_id = row.get("Perfume") or f"perfume_{index}"
        ids.append(doc_id)
        documents.append(build_embedding_text(row))
        embeddings.append(vector)
        metadatas.append(format_metadata(row))

    chroma_db_path = "./chroma_db"
    try:
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        collection = chroma_client.get_or_create_collection(name="fragrances")
        print(f"[寫入中] 正在將 {len(ids)} 筆項目的向量與元數據寫入本地端 ChromaDB...")
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"[✓ 成功] 向量資料庫建置完成。")
        print(f"  • 導入項目數: {len(ids)} 筆")
        print(f"  • 持久化位置: {os.path.abspath(chroma_db_path)}")
        print(f"  • Collection 名稱: fragrances")
    except Exception as e:
        raise RuntimeError(f"ChromaDB 操作失敗: {str(e)}")


if __name__ == "__main__":
    run_ingestion()
