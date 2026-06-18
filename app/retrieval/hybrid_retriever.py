import asyncio
import re
from time import perf_counter_ns

from .common import elapsed_ms, normalize_lancedb_doc, result_ids


def sanitize_fts_text(text: str) -> str:
    cleaned = re.sub(r'["\'’‘“”–—\\/:@#^&*()\[\]{}<>!?|~$%+=,.]+', " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


async def async_vector_search(table, vector, limit):
    started_at = perf_counter_ns()
    results = await asyncio.to_thread(
        lambda: table.search(vector, vector_column_name="embedding").limit(limit).to_list()
    )
    return results, elapsed_ms(started_at)


async def async_fts_search(table, text, limit):
    safe_text = sanitize_fts_text(text)
    started_at = perf_counter_ns()
    results = await asyncio.to_thread(
        lambda: table.search(
            safe_text, fts_columns=["brand", "name", "bm25_text"]
        ).limit(limit).to_list()
    )
    return results, elapsed_ms(started_at)


async def hybrid_retrieve(query: str, top_k: int, engine, ollama_client) -> dict:
    if engine is None or engine.table is None:
        raise RuntimeError("Hybrid retrieval database is not ready.")

    started_at = perf_counter_ns()
    embedding_started_at = perf_counter_ns()
    emb_res = await asyncio.to_thread(
        ollama_client.embed,
        model="nomic-embed-text",
        input=query,
    )
    query_vector = emb_res.get("embeddings", [[]])[0]
    embedding_ms = elapsed_ms(embedding_started_at)
    if not query_vector:
        raise RuntimeError("Failed to generate query embedding.")

    retrieval_started_at = perf_counter_ns()
    vector_search = async_vector_search(engine.table, query_vector, top_k * 2)
    fts_search = async_fts_search(engine.table, query, top_k * 2)
    (hnsw_results, hnsw_ms), (bm25_results, bm25_ms) = await asyncio.gather(
        vector_search, fts_search
    )

    rrf_started_at = perf_counter_ns()
    fused_results = engine._rrf(hnsw_results, bm25_results, k=60)[:top_k]
    rrf_ms = elapsed_ms(rrf_started_at)
    retrieval_total_ms = elapsed_ms(retrieval_started_at)

    normalized_results = [normalize_lancedb_doc(doc) for doc in fused_results]
    retrieved_ids = result_ids(normalized_results)
    return {
        "results": normalized_results,
        "retrievedIds": retrieved_ids,
        "metrics": {
            "embedding_ms": round(embedding_ms, 2),
            "bm25_ms": round(bm25_ms, 2),
            "hnsw_ms": round(hnsw_ms, 2),
            "rrf_ms": round(rrf_ms, 2),
            "retrieval_total_ms": round(retrieval_total_ms, 2),
        },
        "debug": {
            "bm25_top_ids": result_ids(bm25_results),
            "hnsw_top_ids": result_ids(hnsw_results),
            "rrf_top_ids": retrieved_ids,
        },
        "_total_ms": round(elapsed_ms(started_at), 2),
    }
