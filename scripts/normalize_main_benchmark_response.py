import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, Tuple


def normalize_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def load_catalog(path: Path) -> Dict[Tuple[str, str], str]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        sample = source.read(4096)
        source.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        rows = csv.DictReader(source, dialect=dialect)
        catalog = {}
        for row in rows:
            fragrance_id = row.get("id")
            name = row.get("Perfume")
            brand = row.get("Brand")
            if fragrance_id and name and brand:
                catalog[(normalize_key(name), normalize_key(brand))] = fragrance_id
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert the main API response to the benchmark result schema."
    )
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()

    payload = json.load(sys.stdin)
    response = payload["response"]
    latest_metrics = payload["latest_metrics"]
    catalog = load_catalog(args.catalog)

    retrieved_ids = []
    unresolved = []
    for recommendation in response.get("recommendations", []):
        fragrance = recommendation.get("fragrance") or {}
        name = fragrance.get("name")
        brand = fragrance.get("brand")
        response_id = str(fragrance.get("id") or "")
        fragrance_id = (
            response_id
            if re.fullmatch(r"f\d{6}", response_id)
            else catalog.get((normalize_key(name), normalize_key(brand)))
        )
        if fragrance_id:
            retrieved_ids.append(fragrance_id)
        else:
            unresolved.append(f"{name or '<missing name>'} / {brand or '<missing brand>'}")

    if unresolved:
        raise SystemExit(
            "Could not map recommendations to catalog IDs: " + ", ".join(unresolved)
        )

    metrics = latest_metrics.get("metrics") or latest_metrics
    normalized_metrics = {
        "end_to_end_ms": metrics.get("end_to_end_latency_ms"),
        "embedding_ms": metrics.get("embedding_latency_ms"),
        "retrieval_total_ms": metrics.get("retrieval_latency_ms"),
        "llm_generation_ms": metrics.get("llm_generation_latency_ms"),
        "generation_throughput_tokens_sec": metrics.get(
            "generation_throughput_tokens_sec"
        ),
    }

    output = {
        **response,
        "retrieved_ids": retrieved_ids,
        "retrieval_debug": {"retrieved_ids": retrieved_ids},
        "metrics": {
            key: value for key, value in normalized_metrics.items() if value is not None
        },
    }
    json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
