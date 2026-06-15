import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .schemas import KaggleFragranceSchema

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "fra_cleaned_with_id.csv"


def _split_text_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(float(value.replace(",", ".")))
    except ValueError:
        return None


def _parse_float(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def _row_to_schema(row: Dict[str, str]) -> KaggleFragranceSchema:
    normalized = {_normalize_key(k): (v or "").strip() for k, v in row.items()}
    return KaggleFragranceSchema(
        id=normalized.get("id", ""),
        url=normalized.get("url", ""),
        brand=normalized.get("brand", ""),
        name=normalized.get("perfume", ""),
        country=normalized.get("country", ""),
        gender=normalized.get("gender", ""),
        rating_value=_parse_float(normalized.get("rating_value", "")),
        rating_count=_parse_int(normalized.get("rating_count", "")),
        year=_parse_int(normalized.get("year", "")),
        perfumer1=normalized.get("perfumer1", ""),
        perfumer2=normalized.get("perfumer2", ""),
        accords=[normalized.get(f"mainaccord{i}", "") for i in range(1, 6) if normalized.get(f"mainaccord{i}", "")],
        top_notes=_split_text_list(normalized.get("top", "")),
        middle_notes=_split_text_list(normalized.get("middle", "")),
        base_notes=_split_text_list(normalized.get("base", "")),
        description="",
        embedding=None,
    )


def load_kaggle_fragrances(csv_path: Path = CSV_PATH) -> List[KaggleFragranceSchema]:
    """從 CSV 載入香水資料並轉換成 KaggleFragranceSchema。"""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fragrance CSV not found: {csv_path}")

    fragrances: List[KaggleFragranceSchema] = []
    encodings_to_try = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in encodings_to_try:
        try:
            with csv_path.open("r", encoding=enc, newline="") as fp:
                sample = fp.read(4096)
                fp.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.DictReader(fp, dialect=dialect)
                fieldnames = {
                    _normalize_key(name)
                    for name in (reader.fieldnames or [])
                    if name is not None
                }
                required_fields = {"id", "perfume", "brand"}
                missing_fields = required_fields - fieldnames
                if missing_fields:
                    raise ValueError(
                        f"{csv_path} is missing required columns: "
                        f"{', '.join(sorted(missing_fields))}"
                    )
                for row in reader:
                    fragrances.append(_row_to_schema(row))
            print(f"[CSV] 使用編碼 {enc} 成功讀取 {len(fragrances)} 筆資料")
            return fragrances
        except UnicodeDecodeError:
            # 嘗試下一個編碼
            fragrances = []
            continue

    # 最後保守 fallback：替換無法解碼字元，但仍驗證 canonical ID 欄位。
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as fp:
        sample = fp.read(4096)
        fp.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(fp, dialect=dialect)
        for row in reader:
            fragrances.append(_row_to_schema(row))
    print(f"[CSV] 使用 utf-8 + errors=replace 讀取，得到 {len(fragrances)} 筆資料（含替換字元）")
    return fragrances


def iter_kaggle_fragrance_docs(csv_path: Path = CSV_PATH) -> Iterable[Dict[str, object]]:
    """回傳可直接上傳到 LanceDB 的文件產生器。"""
    for item in load_kaggle_fragrances(csv_path):
        yield item.to_lancedb_doc()


if __name__ == "__main__":
    fragrances = load_kaggle_fragrances()
    print(f"Loaded {len(fragrances)} fragrance rows")
    if fragrances:
        print(fragrances[0].dict())
