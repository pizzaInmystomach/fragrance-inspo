async function hybridRetrieve({ query, topK = 5 }) {
  const endpoint = process.env.HYBRID_RETRIEVER_ENDPOINT || "http://127.0.0.1:8000/api/recommend";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: query,
      top_k: topK,
      return_metrics: true,
      return_retrieval_debug: true,
    }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Hybrid retriever failed: ${response.status} ${text}`);
  }

  const payload = await response.json();
  const debug = payload.retrieval_debug || {};
  return {
    results: payload.recommendations || [],
    retrievedIds: debug.retrieved_ids || [],
    metrics: payload.metrics || {},
    debug: {
      bm25_top_ids: debug.bm25_top_ids || [],
      hnsw_top_ids: debug.hnsw_top_ids || [],
      rrf_top_ids: debug.rrf_top_ids || [],
    },
  };
}

module.exports = { hybridRetrieve };
