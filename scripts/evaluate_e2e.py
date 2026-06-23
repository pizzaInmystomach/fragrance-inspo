import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_GOLDEN_PATH = Path("data/golden_dataset_e2e_20.jsonl")
DEFAULT_RESULT_PATH = Path("metrics/e2e-hybrid-local-20.jsonl")
DEFAULT_OUTPUT_PATH = Path("metrics/e2e_evaluation_summary.json")


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}") from error
    return rows


def relevant_ids(row: dict) -> set[str]:
    return {
        str(item.get("perfume_id") or item.get("id"))
        for item in row.get("relevant_perfumes", [])
        if int(item.get("relevance", 0)) >= 2 and (item.get("perfume_id") or item.get("id"))
    }


def average(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def average_or_none(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def result_key(row: dict) -> str:
    return str(row.get("query_id") or row.get("query") or "").strip()


def final_ids(row: dict) -> List[str]:
    debug = row.get("retrieval_debug") or {}
    ids = debug.get("final_recommendation_ids") or row.get("final_recommendation_ids")
    if not ids and row.get("recommendations"):
        ids = [item.get("id") for item in row["recommendations"] if item.get("id")]
    return [str(fragrance_id) for fragrance_id in (ids or [])]


def experiment_config(row: dict) -> dict:
    config = row.get("experiment_config")
    if not isinstance(config, dict):
        raise ValueError("Result row is missing experiment_config.")

    requested = row.get("requested_experiment_config")
    if isinstance(requested, dict):
        expected = {
            "retriever_mode": requested.get("retriever_mode"),
            "llm_mode": requested.get("llm_mode"),
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


def validate_e2e_row(row: dict) -> None:
    config = experiment_config(row)
    if config.get("benchmark_mode") != "e2e":
        raise ValueError(f"E2E evaluator received a non-e2e result row: {config}.")
    if config.get("llm_mode") == "none":
        raise ValueError(f"E2E evaluator received an LLM-disabled result row: {config}.")


def estimate_cost_usd(row: dict) -> Optional[float]:
    metrics = row.get("metrics") or {}
    explicit = row.get(
        "estimated_llm_generation_cost_usd",
        metrics.get("estimated_llm_generation_cost_usd"),
    )
    if explicit is not None:
        return float(explicit)

    input_tokens = row.get("input_tokens", metrics.get("input_tokens"))
    output_tokens = row.get("output_tokens", metrics.get("output_tokens"))
    if input_tokens is None or output_tokens is None:
        return None

    input_rate = float(os.getenv("CLOUD_INPUT_COST_PER_1M_TOKENS", "0.05"))
    output_rate = float(os.getenv("CLOUD_OUTPUT_COST_PER_1M_TOKENS", "0.08"))
    return (float(input_tokens) * input_rate + float(output_tokens) * output_rate) / 1_000_000


def evaluate(golden_rows: List[dict], result_rows: List[dict]) -> dict:
    golden_by_key = {
        result_key(row): row for row in golden_rows if result_key(row)
    }
    hit_at_3 = []
    metrics = {
        "end_to_end_ms": [],
        "retrieval_total_ms": [],
        "llm_generation_ms": [],
        "tokens_per_sec": [],
        "input_tokens": [],
        "output_tokens": [],
        "estimated_llm_generation_cost_saved_usd": [],
        "estimated_cost_saved_per_1000_queries_usd": [],
        "estimated_cost_per_query_usd": [],
    }

    evaluated_count = 0
    for result in result_rows:
        validate_e2e_row(result)
        golden = golden_by_key.get(result_key(result))
        if not golden:
            continue
        expected = relevant_ids(golden)
        actual = final_ids(result)
        hit_at_3.append(int(bool(set(actual[:3]) & expected)))

        nested_metrics = result.get("metrics") or {}
        for key in metrics:
            if key == "estimated_cost_per_query_usd":
                continue
            value = result.get(key, nested_metrics.get(key))
            if value is not None:
                metrics[key].append(float(value))
        cost = estimate_cost_usd(result)
        if cost is not None:
            metrics["estimated_cost_per_query_usd"].append(cost)
        evaluated_count += 1

    avg_input_tokens = average(metrics["input_tokens"])
    avg_output_tokens = average(metrics["output_tokens"])
    avg_saved = average(metrics["estimated_llm_generation_cost_saved_usd"])
    avg_cost = average_or_none(metrics["estimated_cost_per_query_usd"])
    return {
        "evaluated_queries": evaluated_count,
        "final_recommendation_quality": {
            "hit_at_3": average(hit_at_3),
        },
        "latency": {
            "end_to_end_ms": average_or_none(metrics["end_to_end_ms"]),
            "retrieval_total_ms": average_or_none(metrics["retrieval_total_ms"]),
            "llm_generation_ms": average_or_none(metrics["llm_generation_ms"]),
        },
        "tokens": {
            "tokens_per_sec": average_or_none(metrics["tokens_per_sec"]),
            "input_tokens": avg_input_tokens if metrics["input_tokens"] else None,
            "output_tokens": avg_output_tokens if metrics["output_tokens"] else None,
        },
        "cost": {
            "estimated_cost_per_query_usd": avg_cost,
            "estimated_cost_per_1000_queries_usd": (
                avg_cost * 1000 if avg_cost is not None else None
            ),
            "estimated_cost_saved_per_query_usd": avg_saved,
            "estimated_cost_saved_per_1000_queries_usd": average(
                metrics["estimated_cost_saved_per_1000_queries_usd"]
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate E2E benchmark results against the E2E golden subset."
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
