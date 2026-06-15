import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Optional


DEFAULT_INPUT_PATH = Path("data/fra_cleaned_with_id.csv")
DEFAULT_OUTPUT_PATH = Path("data/candidate_pool_for_llm.jsonl")
NOTE_COLUMNS = ("Top", "Middle", "Base")
ACCORD_COLUMNS = tuple(f"mainaccord{i}" for i in range(1, 6))
REQUIRED_COLUMNS = {"id", "Perfume", "Brand", *NOTE_COLUMNS, *ACCORD_COLUMNS}


def clean(value: Optional[str]) -> str:
    return (value or "").strip()


def has_useful_fragrance_data(row: Dict[str, str], min_signal_chars: int) -> bool:
    if not all(clean(row.get(field)) for field in ("id", "Perfume", "Brand")):
        return False

    signal_values = [
        clean(row.get(column))
        for column in (*NOTE_COLUMNS, *ACCORD_COLUMNS)
        if clean(row.get(column))
    ]
    return len(" ".join(signal_values)) >= min_signal_chars


def candidate_from_row(row: Dict[str, str]) -> dict:
    return {
        "id": clean(row.get("id")),
        "perfume": clean(row.get("Perfume")),
        "brand": clean(row.get("Brand")),
        "notes": {
            "top": clean(row.get("Top")),
            "middle": clean(row.get("Middle")),
            "base": clean(row.get("Base")),
        },
        "accords": [
            value
            for column in ACCORD_COLUMNS
            if (value := clean(row.get(column)))
        ],
    }


def iter_candidates(
    input_path: Path, min_signal_chars: int = 20
) -> Iterable[dict]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(
                f"{input_path} is missing required columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        seen_ids = set()
        for row_number, row in enumerate(reader, start=2):
            if not has_useful_fragrance_data(row, min_signal_chars):
                continue

            candidate = candidate_from_row(row)
            fragrance_id = candidate["id"]
            if fragrance_id in seen_ids:
                raise ValueError(
                    f"Duplicate fragrance id {fragrance_id!r} at CSV row {row_number}"
                )
            seen_ids.add(fragrance_id)
            yield candidate


def export_candidate_pool(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    min_signal_chars: int = 20,
    limit: Optional[int] = None,
) -> int:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if min_signal_chars < 0:
        raise ValueError("min_signal_chars must be non-negative")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exported_count = 0
    with output_path.open("w", encoding="utf-8") as destination:
        for candidate in iter_candidates(input_path, min_signal_chars):
            destination.write(json.dumps(candidate, ensure_ascii=False) + "\n")
            exported_count += 1
            if limit is not None and exported_count >= limit:
                break

    return exported_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export canonical fragrance candidates for LLM annotation."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--min-signal-chars", type=int, default=20)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    count = export_candidate_pool(
        input_path=args.input,
        output_path=args.output,
        min_signal_chars=args.min_signal_chars,
        limit=args.limit,
    )
    print(f"Candidate rows: {count}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
