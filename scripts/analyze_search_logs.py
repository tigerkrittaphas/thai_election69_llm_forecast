#!/usr/bin/env python3
"""Analyze weekly search logs for source coverage and diversity."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_log_files(paths: List[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for child in path.rglob("*.json"):
                yield child
        else:
            yield path


def normalize_publisher(publisher: str) -> str:
    return " ".join(publisher.split()).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze search log JSON files.")
    parser.add_argument("paths", nargs="+", help="Search log JSON files or directories.")
    parser.add_argument("--out-dir", default="data/analysis", help="Output directory for CSVs.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: List[Dict[str, str]] = []
    publisher_rows: List[Dict[str, str]] = []
    duplicate_index: Dict[Tuple[str, str], Dict[str, object]] = {}

    total_logs = 0
    total_sources = 0

    for path in iter_log_files(args.paths):
        if not path.exists():
            print(f"Missing file: {path}")
            continue
        data = load_json(path)
        total_logs += 1

        week_start = data.get("week_start", "")
        week_end = data.get("week_end", "")
        model = data.get("model", "")
        queries = data.get("queries", [])
        sources = data.get("sources", [])
        excluded = data.get("excluded_sources", [])

        total_sources += len(sources)

        publisher_counts: Counter = Counter()
        for src in sources:
            publisher = normalize_publisher(str(src.get("publisher", "Unknown")))
            publisher_counts[publisher] += 1

            url = str(src.get("url", ""))
            title = str(src.get("title", ""))
            dup_key = (week_start, url)
            if url:
                entry = duplicate_index.setdefault(dup_key, {"title": title, "models": set()})
                entry["models"].add(model)

        summary_rows.append({
            "week_start": week_start,
            "week_end": week_end,
            "model": model,
            "source_count": str(len(sources)),
            "unique_publishers": str(len(publisher_counts)),
            "query_count": str(len(queries)),
            "excluded_count": str(len(excluded))
        })

        for publisher, count in publisher_counts.items():
            publisher_rows.append({
                "week_start": week_start,
                "week_end": week_end,
                "model": model,
                "publisher": publisher,
                "count": str(count)
            })

    summary_path = out_dir / "search_summary.csv"
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "week_start",
            "week_end",
            "model",
            "source_count",
            "unique_publishers",
            "query_count",
            "excluded_count"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)

    publisher_path = out_dir / "publisher_counts.csv"
    with publisher_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "week_start",
            "week_end",
            "model",
            "publisher",
            "count"
        ])
        writer.writeheader()
        writer.writerows(publisher_rows)

    duplicates_path = out_dir / "duplicate_urls.csv"
    with duplicates_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "week_start",
            "url",
            "title",
            "models_count",
            "models"
        ])
        writer.writeheader()
        for (week_start, url), entry in sorted(duplicate_index.items()):
            models = sorted(m for m in entry["models"] if m)
            if len(models) < 2:
                continue
            writer.writerow({
                "week_start": week_start,
                "url": url,
                "title": entry.get("title", ""),
                "models_count": str(len(models)),
                "models": ",".join(models)
            })

    print(f"Logs processed: {total_logs}")
    print(f"Total sources: {total_sources}")
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {publisher_path}")
    print(f"Wrote: {duplicates_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
