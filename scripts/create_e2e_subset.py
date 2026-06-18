import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List


DEFAULT_INPUT_PATH = Path("data/golden_dataset.jsonl")
DEFAULT_OUTPUT_PATH = Path("data/golden_dataset_e2e_20.jsonl")
DEFAULT_DISTRIBUTION = {
    "exact_name": 2,
    "brand_exact": 2,
    "note_exact": 4,
    "semantic_mood": 4,
    "occasion": 3,
    "negative_constraint": 3,
    "abstract_style": 2,
}


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


def create_subset(rows: List[dict], distribution: Dict[str, int]) -> List[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get("query_type", "")].append(row)

    selected = []
    for query_type, count in distribution.items():
        available = grouped.get(query_type, [])
        if len(available) < count:
            raise ValueError(
                f"Need {count} rows for query_type={query_type!r}, "
                f"but only found {len(available)}."
            )
        selected.extend(available[:count])

    original_order = {row.get("query_id"): index for index, row in enumerate(rows)}
    selected.sort(key=lambda row: original_order.get(row.get("query_id"), 10**9))
    return selected


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as destination:
        for row in rows:
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a stratified 20-query E2E subset from the golden dataset."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    subset = create_subset(rows, DEFAULT_DISTRIBUTION)
    write_jsonl(args.output, subset)

    counts = Counter(row["query_type"] for row in subset)
    print(json.dumps({"rows": len(subset), "query_type_counts": counts}, indent=2))
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
