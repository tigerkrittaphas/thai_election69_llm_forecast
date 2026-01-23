#!/usr/bin/env python3
"""Validate forecast JSON files for seat totals and consistency."""

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_int(value) -> bool:
    return isinstance(value, int)


def validate_file(path: Path, party_list_total: int, district_total: int, total_seats: int) -> List[str]:
    errors: List[str] = []
    data = load_json(path)

    for key in ("forecast_party_list", "forecast_district", "forecast_total"):
        if key not in data:
            errors.append(f"Missing '{key}'.")
            return errors

    party_list = data["forecast_party_list"]
    district = data["forecast_district"]
    total = data["forecast_total"]

    parties = list(party_list.keys())
    if set(parties) != set(district.keys()) or set(parties) != set(total.keys()):
        errors.append("Party keys do not match across sections.")
        return errors

    for party in parties:
        for section_name, section in (
            ("forecast_party_list", party_list),
            ("forecast_district", district),
            ("forecast_total", total),
        ):
            value = section.get(party)
            if not is_int(value):
                errors.append(f"{section_name}.{party} is not an integer.")
            elif value < 0:
                errors.append(f"{section_name}.{party} is negative.")

    if sum(party_list.values()) != party_list_total:
        errors.append(f"Party-list sum {sum(party_list.values())} != {party_list_total}.")
    if sum(district.values()) != district_total:
        errors.append(f"District sum {sum(district.values())} != {district_total}.")
    if sum(total.values()) != total_seats:
        errors.append(f"Total sum {sum(total.values())} != {total_seats}.")

    for party in parties:
        if party_list[party] + district[party] != total[party]:
            errors.append(f"Total mismatch for {party}.")

    return errors


def expand_paths(paths: List[str]) -> List[Path]:
    expanded: List[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            expanded.extend(path.rglob("*.json"))
        else:
            expanded.append(path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate forecast JSON files.")
    parser.add_argument("paths", nargs="+", help="Forecast JSON files or directories.")
    parser.add_argument("--party-list-seats", type=int, default=100)
    parser.add_argument("--district-seats", type=int, default=400)
    parser.add_argument("--total-seats", type=int, default=500)
    args = parser.parse_args()

    errors_found = False
    for path in expand_paths(args.paths):
        if not path.exists():
            print(f"Missing file: {path}")
            errors_found = True
            continue
        errors = validate_file(path, args.party_list_seats, args.district_seats, args.total_seats)
        if errors:
            errors_found = True
            print(f"{path}:")
            for err in errors:
                print(f"  - {err}")

    return 1 if errors_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
