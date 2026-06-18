import csv
import re
from functools import lru_cache
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, Iterable, List, Optional


DATA_PATH = Path("data/fra_cleaned_with_id.csv")
NOTE_COLUMNS = ("Top", "Middle", "Base")
ACCORD_COLUMNS = tuple(f"mainaccord{index}" for index in range(1, 6))


def elapsed_ms(start_ns: int) -> float:
    return (perf_counter_ns() - start_ns) / 1_000_000


def clean(value: Optional[object]) -> str:
    return str(value or "").strip()


def tokenize(value: object) -> List[str]:
    text = clean(value).lower()
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?|[\u4e00-\u9fff]+", text)


def result_ids(results: Iterable[dict]) -> List[str]:
    return [str(result["id"]) for result in results if result.get("id") is not None]


def normalize_row(row: Dict[str, str]) -> dict:
    accords = [clean(row.get(column)) for column in ACCORD_COLUMNS if clean(row.get(column))]
    top_notes = clean(row.get("Top"))
    middle_notes = clean(row.get("Middle"))
    base_notes = clean(row.get("Base"))
    return {
        "id": clean(row.get("id")),
        "name": clean(row.get("Perfume") or row.get("name")),
        "brand": clean(row.get("Brand") or row.get("brand")),
        "url": clean(row.get("url")),
        "country": clean(row.get("Country")),
        "gender": clean(row.get("Gender")),
        "rating_value": clean(row.get("Rating Value")),
        "rating_count": clean(row.get("Rating Count")),
        "year": clean(row.get("Year")),
        "accords": accords,
        "top_notes": [item.strip() for item in top_notes.split(",") if item.strip()],
        "middle_notes": [item.strip() for item in middle_notes.split(",") if item.strip()],
        "base_notes": [item.strip() for item in base_notes.split(",") if item.strip()],
        "description": " ".join(
            part
            for part in (
                " ".join(accords),
                top_notes,
                middle_notes,
                base_notes,
            )
            if part
        ),
        "_raw": row,
    }


@lru_cache(maxsize=1)
def load_fragrance_rows(path: str = str(DATA_PATH)) -> List[dict]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"id", "Perfume", "Brand", *NOTE_COLUMNS, *ACCORD_COLUMNS}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{csv_path} is missing required columns: {', '.join(sorted(missing))}"
            )
        rows = [normalize_row(row) for row in reader]

    seen = set()
    unique_rows = []
    for row in rows:
        fragrance_id = row.get("id")
        if not fragrance_id or fragrance_id in seen:
            continue
        seen.add(fragrance_id)
        unique_rows.append(row)
    return unique_rows


def normalize_lancedb_doc(doc: dict) -> dict:
    metadata = doc.get("metadata") or {}
    return {
        "id": clean(doc.get("id")),
        "name": clean(doc.get("name") or metadata.get("name")),
        "brand": clean(doc.get("brand") or metadata.get("brand")),
        "url": clean(doc.get("url") or metadata.get("url")),
        "country": metadata.get("country", ""),
        "gender": metadata.get("gender", ""),
        "rating_value": metadata.get("rating_value"),
        "rating_count": metadata.get("rating_count"),
        "year": metadata.get("year"),
        "accords": metadata.get("accords") or [],
        "top_notes": metadata.get("top_notes") or [],
        "middle_notes": metadata.get("middle_notes") or [],
        "base_notes": metadata.get("base_notes") or [],
        "description": clean(doc.get("description") or metadata.get("description") or doc.get("bm25_text")),
    }
