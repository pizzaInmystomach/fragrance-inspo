import inspect
import lancedb
from typing import List, Dict, Any

class HybridSearchEngine:
    def __init__(self, db_path: str = "./lancedb_data", table_name: str = "fragrances"):
        self.db_path = db_path
        self.table_name = table_name
        self.db = lancedb.connect(self.db_path)
        self.table = None
        
        # 檢查資料表是否已存在
        if self.table_name in self.db.table_names():
            self.table = self.db.open_table(self.table_name)

    def create_hybrid_indices(self):
        """
        為現有的資料表建置雙軌索引：HNSW 向量索引與 BM25 全文檢索索引
        """
        if self.table is None:
            raise ValueError(f"資料表 {self.table_name} 不存在，無法建置索引。")

        print("[系統訊息] 開始配置 HNSW 密集向量索引...")
        # 針對 16GB RAM 優化的 HNSW 參數：降低 M 與 ef_construction 以防止記憶體溢出
        # Diagnostic: print table schema to understand available fields
        try:
            schema = getattr(self.table, "schema", None)
            if schema is not None:
                # pyarrow Schema has names attribute
                names = getattr(schema, "names", None)
                print(f"[診斷] 表欄位: {names}")
            else:
                print("[診斷] 無法取得 table.schema")
        except Exception as e:
            print(f"[診斷] 讀取 schema 失敗: {e}")

        # Try to detect vector column name (embedding, vector, embeddings, vec)
        possible_vector_cols = ["embedding", "vector", "embeddings", "vec"]
        detected_col = None
        try:
            schema_names = getattr(self.table.schema, "names", []) or []
            for c in possible_vector_cols:
                if c in schema_names:
                    detected_col = c
                    break
            if detected_col:
                print(f"[診斷] 偵測到向量欄位: {detected_col}，嘗試建立向量索引...")
                # Inspect create_index signature to call in a compatible way across lancedb versions
                try:
                    create_index_fn = getattr(self.table, "create_index")
                    sig = inspect.signature(create_index_fn)
                    params = list(sig.parameters.keys())

                    # Build kwargs depending on available parameter names
                    kwargs = {}
                    if "column" in params:
                        kwargs["column"] = detected_col
                    elif "field" in params:
                        kwargs["field"] = detected_col
                    elif "vector_column_name" in params:
                        # lancedb v0.17 uses 'vector_column_name' param
                        kwargs["vector_column_name"] = detected_col
                    else:
                        # fallback to positional
                        kwargs = {"_pos0": detected_col}

                    # prefer setting metric/method if supported
                    if "metric" in params:
                        kwargs["metric"] = "cosine"
                    if "method" in params and "method" not in kwargs:
                        kwargs["method"] = "hnsw"
                    # memory-friendly HNSW params when available
                    if "m" in params:
                        kwargs["m"] = 8
                    if "ef_construction" in params:
                        kwargs["ef_construction"] = 100
                    if "num_sub_vectors" in params:
                        kwargs["num_sub_vectors"] = 96

                    # Attempt call: prefer keyword args; if we had to fallback to positional, call accordingly
                    try:
                        if "_pos0" in kwargs:
                            # positional-only fallback
                            create_index_fn(kwargs.pop("_pos0"))
                        else:
                            create_index_fn(**kwargs)
                        print(f"[系統訊息] 向量索引建立成功 (column={detected_col})")
                    except TypeError as e_pos:
                        # As a final fallback, try calling with only the column name positionally
                        try:
                            create_index_fn(detected_col)
                            print(f"[系統訊息] 向量索引建立成功 (fallback positional, column={detected_col})")
                        except Exception as e_final:
                            print(f"[警告] 嘗試多種方式建立向量索引均失敗: {e_final}")
                except Exception as e:
                    print(f"[警告] 建立向量索引時發生例外: {e}")
            else:
                print("[診斷] 未偵測到向量欄位，跳過向量索引建立 (可手動建立)")
        except Exception as e:
            print(f"[診斷] 建立向量索引時發生例外: {e}")

        print("[系統訊息] 開始配置 BM25 全文檢索索引...")
        # 為指定文字欄位建立全文檢索（FTS）索引，使用目前存在於 schema 的欄位
        try:
            desired_fts = ["brand", "name", "bm25_text"]
            available = getattr(self.table.schema, "names", []) or []
            fts_fields = [c for c in desired_fts if c in available]
            if not fts_fields:
                print("[診斷] 找不到可用的 FTS 欄位，跳過 FTS 建索引")
            else:
                print(f"[診斷] 將為下列欄位建立 FTS: {fts_fields}")
                self.table.create_fts_index(fts_fields, replace=True)
                print("[系統訊息] BM25 FTS 索引建立成功")
        except Exception as e:
            print(f"[警告] BM25 FTS 索引建立失敗: {e}")
            print("[系統訊息] 繼續進行，FTS 索引可稍後手動執行或使用預設設定")
        print("[系統訊息] 雙軌混合索引建置完畢。")

    def _rrf(self, vector_results: List[Dict[str, Any]], fts_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """
        實作倒數排名融合 (Reciprocal Rank Fusion) 演算法
        """
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # 處理向量檢索排名
        for rank, doc in enumerate(vector_results):
            doc_id = str(doc["id"])
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + (rank + 1))

        # 處理全文檢索排名
        for rank, doc in enumerate(fts_results):
            doc_id = str(doc["id"])
            doc_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + (rank + 1))

        # 依據 RRF 分數由高到低排序
        sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        
        # 回傳排序後的原始文件資料
        return [doc_map[doc_id] for doc_id, score in sorted_docs]

    def search(self, query_text: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        執行雙軌並行查詢並進行 RRF 融合
        """
        if self.table is None:
            raise ValueError("資料表未初始化。")

        # 軌道一：密集向量檢索 (HNSW)
        vector_res = self.table.search(query_vector, column="embedding").limit(limit * 2).to_list()

        # 軌道二：稀疏向量檢索 (BM25 全文檢索)
        # 只搜尋實際存在於 table schema 的欄位
        schema_names = getattr(self.table.schema, "names", []) or []
        fts_cols = [c for c in ["brand", "name", "bm25_text"] if c in schema_names]
        if fts_cols:
            fts_res = self.table.search(query_text, columns=fts_cols).limit(limit * 2).to_list()
        else:
            fts_res = []

        # 進行融合重排
        final_results = self._rrf(vector_res, fts_res, k=60)
        
        return final_results[:limit]