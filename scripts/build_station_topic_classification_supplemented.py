from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TOPIC_PATH = DATA_DIR / "station_topic_classification.csv"
LOOKUP_PATH = DATA_DIR / "mrt_station_codes.csv"
OD_DIR = DATA_DIR / "od_subset"
OUTPUT_PATH = DATA_DIR / "station_topic_classification_supplemented.csv"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    topic_rows = load_csv(TOPIC_PATH)
    fieldnames = list(topic_rows[0].keys())
    extra_fields = ["supplemented_from", "supplemented_station_name", "supplemented_via_compound"]
    output_fields = fieldnames + [f for f in extra_fields if f not in fieldnames]

    by_code: OrderedDict[str, dict[str, str]] = OrderedDict()
    for row in topic_rows:
        code = row["station_code"]
        if code not in by_code:
            by_code[code] = row

    lookup_rows = load_csv(LOOKUP_PATH)
    code_to_station = {row["stn_code"]: row["station_name"] for row in lookup_rows}

    compound_codes: set[str] = set()
    for path in sorted(OD_DIR.glob("origin_destination_train_*.csv")):
        for row in load_csv(path):
            for key in ("ORIGIN_PT_CODE", "DESTINATION_PT_CODE"):
                code = row[key]
                if "/" in code:
                    compound_codes.add(code)

    added_rows: list[dict[str, str]] = []
    for compound in sorted(compound_codes):
        parts = [part for part in compound.split("/") if part]
        existing_parts = [part for part in parts if part in by_code]
        if not existing_parts:
            continue

        source_code = existing_parts[0]
        source_row = by_code[source_code]
        station_name = code_to_station.get(source_code, "")

        for part in parts:
            if part in by_code:
                continue
            new_row = dict(source_row)
            new_row["station_code"] = part
            new_row["supplemented_from"] = source_code
            new_row["supplemented_station_name"] = station_name
            new_row["supplemented_via_compound"] = compound
            by_code[part] = new_row
            added_rows.append(new_row)

    output_rows: list[dict[str, str]] = []
    for row in by_code.values():
        out = dict(row)
        for field in extra_fields:
            out.setdefault(field, "")
        output_rows.append(out)

    output_rows.sort(key=lambda row: row["station_code"])
    write_csv(OUTPUT_PATH, output_rows, output_fields)

    print(f"Saved {OUTPUT_PATH}")
    print(f"Original rows: {len(topic_rows)}")
    print(f"Added single-code aliases: {len(added_rows)}")
    for row in added_rows:
        print(
            row["station_code"],
            row.get("label", ""),
            row.get("supplemented_from", ""),
            row.get("supplemented_via_compound", ""),
        )


if __name__ == "__main__":
    main()
