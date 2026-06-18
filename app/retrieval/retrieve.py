import os

from .baseline_retriever import baseline_retrieve
from .hybrid_retriever import hybrid_retrieve


VALID_RETRIEVER_MODES = {"baseline", "hybrid"}


async def retrieve(query: str, top_k: int = 5, *, engine=None, ollama_client=None) -> dict:
    mode = os.getenv("RETRIEVER_MODE", "hybrid").strip().lower()
    if mode == "baseline":
        return baseline_retrieve(query=query, top_k=top_k)
    if mode == "hybrid":
        return await hybrid_retrieve(
            query=query,
            top_k=top_k,
            engine=engine,
            ollama_client=ollama_client,
        )
    raise ValueError(
        f"Unknown RETRIEVER_MODE={mode!r}. Expected one of: "
        f"{', '.join(sorted(VALID_RETRIEVER_MODES))}."
    )
