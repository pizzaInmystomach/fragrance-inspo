from collections import Counter
from time import perf_counter_ns
from typing import Dict, List

from .common import elapsed_ms, load_fragrance_rows, result_ids, tokenize


STOP_WORDS = {
    "about",
    "after",
    "before",
    "can",
    "find",
    "fragrance",
    "looking",
    "need",
    "notes",
    "perfume",
    "please",
    "recommend",
    "scent",
    "something",
    "that",
    "this",
    "want",
    "with",
    "would",
}

SYNONYM_MAP = {
    "paper-like": ["paper", "papyrus"],
    "earthy": ["earth", "soil", "moss", "patchouli", "vetiver"],
    "damp": ["moss", "aquatic", "mineral"],
    "woody": ["wood", "cedar", "sandalwood"],
    "rainy": ["aquatic", "ozonic", "mineral"],
    "smoky": ["smoke", "incense"],
}

WEIGHTED_FIELDS = (
    ("accords", 4.0),
    ("top_notes", 3.0),
    ("middle_notes", 3.0),
    ("base_notes", 3.0),
    ("name", 2.5),
    ("brand", 1.5),
    ("description", 1.0),
)


def _query_terms(query: str) -> List[str]:
    terms = [term for term in tokenize(query) if term not in STOP_WORDS]
    for term in list(terms):
        terms.extend(SYNONYM_MAP.get(term, []))
    return list(dict.fromkeys(terms))


def _score_row(row: Dict[str, object], query_counts: Counter) -> float:
    score = 0.0
    for field, weight in WEIGHTED_FIELDS:
        field_terms = Counter(tokenize(row.get(field, "")))
        score += weight * sum(
            min(count, field_terms.get(term, 0))
            for term, count in query_counts.items()
        )
    return score


def baseline_retrieve(query: str, top_k: int = 5) -> dict:
    started_at = perf_counter_ns()
    baseline_started_at = perf_counter_ns()
    rows = load_fragrance_rows()
    query_counts = Counter(_query_terms(query))

    scored = []
    for position, row in enumerate(rows):
        score = _score_row(row, query_counts)
        scored.append((score, -position, row))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    results = [row for _, _, row in scored[:top_k]]
    baseline_ms = elapsed_ms(baseline_started_at)

    retrieved_ids = result_ids(results)
    return {
        "results": results,
        "retrievedIds": retrieved_ids,
        "metrics": {
            "retrieval_total_ms": round(elapsed_ms(started_at), 2),
            "baseline_ms": round(baseline_ms, 2),
        },
        "debug": {
            "baseline_top_ids": retrieved_ids,
        },
    }
