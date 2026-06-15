import gc
import ollama
import lancedb
import numpy as np
import pyarrow as pa
from typing import List, Dict, Any

from app.csv_loader import CSV_PATH, load_kaggle_fragrances
from app.search_engine import HybridSearchEngine

# 配置參數
BATCH_SIZE = 500  # 每批次處理 500 筆，平衡 M3 記憶體與處理速度
EMBEDDING_MODEL = "nomic-embed-text"
SAMPLE_FRACTION = 1.0  # 設為 1.0 使用全部資料；設為 0.1 只用前 10%（測試用）


def _get_memory_usage_mb() -> float:
    """Return current process memory usage in MB. Uses psutil if available, else resource fallback."""
    try:
        import psutil

        return psutil.Process().memory_info().rss / 1024 ** 2
    except Exception:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss: on Linux it's in KB, on macOS it's in bytes. Heuristic conversion:
        if usage > 1024 * 1024:
            # likely bytes
            return usage / 1024 ** 2
        else:
            # likely KB
            return usage / 1024.0


def process_batch_with_embeddings(schemas: List) -> List[Dict[str, Any]]:
    """處理單個批次：呼叫 Ollama Embedding 並組裝 LanceDB 寫入格式"""
    if not schemas:
        return []

    # 提取待向量化的文本清單
    texts_to_embed = [s.to_embedding_text() for s in schemas]

    # 調用本地 Ollama nomic-embed-text 模型
    # 16GB RAM 環境下，Ollama 會在本地記憶體內處理此批次文本
    print(f"[Embedding] 正在向量化 {len(texts_to_embed)} 筆文本...")
    response = ollama.embed(model=EMBEDDING_MODEL, input=texts_to_embed)
    embeddings = response.get("embeddings", [])

    if not embeddings:
        print("[警告] Ollama 未回傳 embeddings，跳過此批次")
        return []

    # 組裝符合 LanceDB 規格的寫入字典清單
    table_records = []
    embedding_dim = len(embeddings[0]) if embeddings else 0
    for schema, vector in zip(schemas, embeddings):
        doc = schema.to_lancedb_doc()
        # Convert to float32 numpy array so we can make a fixed-size vector scalar
        try:
            vec32 = np.asarray(vector, dtype=np.float32)
            vec_scalar = pa.array([vec32], type=pa.list_(pa.float32(), embedding_dim))[0]
        except Exception:
            vec_scalar = vector
        doc["embedding"] = vec_scalar
        table_records.append(doc)

    return table_records

def run_ingestion():
    """流式讀取 CSV、向量化、批次寫入 LanceDB、建置混合索引"""
    print("[系統訊息] Initialize LanceDB Connection...")
    db = lancedb.connect("./lancedb_data")
    table_name = "fragrances"
    table = None

    print("[系統訊息] 從 CSV 載入香水資料...")
    all_schemas = load_kaggle_fragrances(CSV_PATH)
    
    # 若 SAMPLE_FRACTION < 1.0，只取樣本資料進行測試
    if SAMPLE_FRACTION < 1.0:
        sample_count = max(1, int(len(all_schemas) * SAMPLE_FRACTION))
        all_schemas = all_schemas[:sample_count]
        print(f"[測試模式] 只使用前 {sample_count} 筆資料（全部 {len(all_schemas)} 筆的 {SAMPLE_FRACTION*100:.0f}%）")
    
    total_count = len(all_schemas)
    print(f"[系統訊息] 成功載入 {total_count} 筆香水資料")

    print(f"[系統訊息] 開始以每批 {BATCH_SIZE} 筆進行向量化與寫入...")

    total_inserted = 0
    batch_count = 1

    # 分批處理
    for i in range(0, total_count, BATCH_SIZE):
        batch_schemas = all_schemas[i : i + BATCH_SIZE]
        print(f"\n[批次 {batch_count}] 處理第 {i} - {min(i + BATCH_SIZE, total_count)} 筆...")

        records = process_batch_with_embeddings(batch_schemas)
        if records:
            if table is None:
                # 第一批次：動態建立資料表
                print("[系統訊息] 建立 LanceDB 資料表...")
                table = db.create_table(table_name, data=records, mode="overwrite")
            else:
                # 後續批次：直接追加寫入硬碟實體檔案
                table.add(records)

            total_inserted += len(records)
            print(f"[寫入完成] 已導入 {len(records)} 筆，累計 {total_inserted} 筆...")
            mem_mb = _get_memory_usage_mb()
            print(f"[MEM] 目前記憶體使用量: {mem_mb:.1f} MB")

        # 強制釋放記憶體，防止 16GB Mac 記憶體堆積
        gc.collect()
        batch_count += 1

    print(f"\n[系統訊息] 所有資料寫入完成，總計導入 {total_inserted} 筆。")

    # 資料全部寫入硬碟後，啟動混合索引建置
    print("\n[系統訊息] 進入混合索引建置階段...")
    mem_mb = _get_memory_usage_mb()
    print(f"[MEM] 建置索引前記憶體使用量: {mem_mb:.1f} MB")
    engine = HybridSearchEngine()
    engine.create_hybrid_indices()
    mem_mb = _get_memory_usage_mb()
    print(f"[MEM] 建置索引後記憶體使用量: {mem_mb:.1f} MB")
    print("[系統訊息] 階段三資料流式導入與混合索引建置完全成功！")

if __name__ == "__main__":
    run_ingestion()
