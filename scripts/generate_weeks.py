#!/usr/bin/env python3
"""Generate weekly windows for the study."""

import argparse
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate weekly windows.")
    parser.add_argument("--start", default="2025-12-12", help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD). Defaults to today in timezone.")
    parser.add_argument("--timezone", default="Asia/Bangkok", help="Timezone for 'today'.")
    parser.add_argument("--out", default="data/weeks.csv", help="Output CSV path.")
    args = parser.parse_args()

    tz = ZoneInfo(args.timezone)
    start_date = parse_date(args.start)
    if args.end:
        end_date = parse_date(args.end)
    else:
        end_date = datetime.now(tz).date()

    if end_date < start_date:
        raise SystemExit("End date is before start date.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    week_index = 0
    current = start_date
    while current <= end_date:
        week_start = current
        week_end = min(current + timedelta(days=6), end_date)
        rows.append({
            "week_index": week_index,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat()
        })
        week_index += 1
        current = current + timedelta(days=7)

    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["week_index", "week_start", "week_end"])
        writer.writeheader()
        writer.writerows(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
