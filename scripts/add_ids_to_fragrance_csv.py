import argparse
import csv
import io
from pathlib import Path


DEFAULT_INPUT_PATH = Path("data/fra_cleaned.csv")
DEFAULT_OUTPUT_PATH = Path("data/fra_cleaned_with_id.csv")


def read_source_text(input_path: Path) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return input_path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Unable to decode CSV: {input_path}")


def add_ids(input_path: Path, output_path: Path) -> int:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    source_text, encoding = read_source_text(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with io.StringIO(source_text, newline="") as source:
        reader = csv.DictReader(source, delimiter=";")
        source_fields = [
            field for field in (reader.fieldnames or []) if field and field != "id"
        ]
        if not source_fields:
            raise ValueError(f"No CSV columns found in {input_path}")

        with output_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as destination:
            writer = csv.DictWriter(
                destination, fieldnames=["id", *source_fields]
            )
            writer.writeheader()
            row_count = 0
            for row_count, row in enumerate(reader, start=1):
                output_row = {
                    field: row.get(field, "") for field in source_fields
                }
                output_row["id"] = f"f{row_count:06d}"
                writer.writerow(output_row)

    print(f"Source encoding: {encoding}")
    return row_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add deterministic canonical IDs to the fragrance CSV."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    count = add_ids(args.input, args.output)
    print(f"Rows: {count}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
