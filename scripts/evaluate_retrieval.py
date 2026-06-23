import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_GOLDEN_PATH = Path("data/golden_dataset.jsonl")
DEFAULT_RESULT_PATH = Path("metrics/fragrance_request_metrics-feature.jsonl")
DEFAULT_OUTPUT_PATH = Path("metrics/evaluation_summary.json")
K_VALUES = (3, 5)


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}"
                ) from error
    return rows


def relevant_map(golden_item: dict) -> Dict[str, int]:
    relevant = {}
    for item in golden_item.get("relevant_perfumes", []):
        fragrance_id = item.get("perfume_id") or item.get("id")
        if fragrance_id:
            relevant[str(fragrance_id)] = int(item.get("relevance", 0))
    return relevant


def relevant_ids(relevance_by_id: Dict[str, int]) -> set:
    return {
        fragrance_id
        for fragrance_id, relevance in relevance_by_id.items()
        if relevance >= 2
    }


def hit_at_k(
    retrieved: List[str], relevance_by_id: Dict[str, int], k: int
) -> int:
    return int(bool(set(retrieved[:k]) & relevant_ids(relevance_by_id)))


def recall_at_k(
    retrieved: List[str], relevance_by_id: Dict[str, int], k: int
) -> float:
    expected = relevant_ids(relevance_by_id)
    return len(set(retrieved[:k]) & expected) / len(expected) if expected else 0.0


def reciprocal_rank(
    retrieved: List[str], relevance_by_id: Dict[str, int]
) -> float:
    expected = relevant_ids(relevance_by_id)
    for rank, fragrance_id in enumerate(retrieved, start=1):
        if fragrance_id in expected:
            return 1.0 / rank
    return 0.0


def dcg(relevances: Iterable[int]) -> float:
    return sum(
        (2 ** relevance - 1) / math.log2(rank + 1)
        for rank, relevance in enumerate(relevances, start=1)
    )


def ndcg_at_k(
    retrieved: List[str], relevance_by_id: Dict[str, int], k: int
) -> float:
    actual = dcg(relevance_by_id.get(fragrance_id, 0) for fragrance_id in retrieved[:k])
    ideal = dcg(sorted(relevance_by_id.values(), reverse=True)[:k])
    return actual / ideal if ideal else 0.0


def average(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def average_or_none(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def result_key(row: dict) -> str:
    return str(row.get("query_id") or row.get("query") or "").strip()


def golden_key(row: dict) -> str:
    return str(row.get("query_id") or row.get("query") or "").strip()


def experiment_config(row: dict) -> dict:
    config = row.get("experiment_config")
    if not isinstance(config, dict):
        raise ValueError("Result row is missing experiment_config.")

    requested = row.get("requested_experiment_config")
    if isinstance(requested, dict):
        expected = {
            "retriever_mode": requested.get("retriever_mode"),
            "llm_mode": "none"
            if requested.get("benchmark_mode") == "retrieval_only"
            else requested.get("llm_mode"),
            "benchmark_mode": requested.get("benchmark_mode"),
        }
        actual = {
            "retriever_mode": config.get("retriever_mode"),
            "llm_mode": config.get("llm_mode"),
            "benchmark_mode": config.get("benchmark_mode"),
        }
        if actual != expected:
            raise ValueError(
                f"Result row experiment_config {actual} does not match requested {expected}."
            )
    return config


def validate_retrieval_only_row(row: dict) -> None:
    config = experiment_config(row)
    if config.get("benchmark_mode") != "retrieval_only":
        raise ValueError(
            "Retrieval evaluator received a non-retrieval-only result row: "
            f"{config}."
        )

    metrics = row.get("metrics") or {}
    for key in ("llm_generation_ms", "input_tokens", "output_tokens", "tokens_per_sec"):
        value = row.get(key, metrics.get(key))
        if value is not None and value != 0:
            raise ValueError(
                f"Retrieval-only result contains LLM metric {key}={value!r}."
            )


def evaluate(golden_rows: List[dict], result_rows: List[dict]) -> dict:
    golden_by_key = {
        key: row for row in golden_rows if (key := golden_key(row))
    }
    quality = {
        "mrr": [],
        **{f"hit_at_{k}": [] for k in K_VALUES},
        **{f"recall_at_{k}": [] for k in K_VALUES},
        **{f"ndcg_at_{k}": [] for k in K_VALUES},
    }
    latency_keys = (
        "end_to_end_ms",
        "embedding_ms",
        "baseline_ms",
        "bm25_ms",
        "hnsw_ms",
        "rrf_ms",
        "retrieval_total_ms",
    )
    latencies = {key: [] for key in latency_keys}
    evaluated_count = 0

    for result in result_rows:
        validate_retrieval_only_row(result)
        golden = golden_by_key.get(result_key(result))
        if golden is None:
            continue

        relevance_by_id = relevant_map(golden)
        retrieval_debug = result.get("retrieval_debug") or {}
        retrieved = retrieval_debug.get("retrieved_ids") or result.get("retrieved_ids") or []
        retrieved = [str(fragrance_id) for fragrance_id in retrieved]

        quality["mrr"].append(reciprocal_rank(retrieved, relevance_by_id))
        for k in K_VALUES:
            quality[f"hit_at_{k}"].append(hit_at_k(retrieved, relevance_by_id, k))
            quality[f"recall_at_{k}"].append(
                recall_at_k(retrieved, relevance_by_id, k)
            )
            quality[f"ndcg_at_{k}"].append(
                ndcg_at_k(retrieved, relevance_by_id, k)
            )

        nested_metrics = result.get("metrics") or {}
        for key in latency_keys:
            value = result.get(key, nested_metrics.get(key))
            if value is not None:
                latencies[key].append(float(value))
        evaluated_count += 1

    return {
        "evaluated_queries": evaluated_count,
        "retrieval_quality": {
            key: average(values) for key, values in quality.items()
        },
        "latency": {
            **{key: average_or_none(values) for key, values in latencies.items()},
            "llm_generation_ms": None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval metrics against a golden JSONL dataset."
    )
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    summary = evaluate(load_jsonl(args.golden), load_jsonl(args.results))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as destination:
        json.dump(summary, destination, ensure_ascii=False, indent=2)
        destination.write("\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
