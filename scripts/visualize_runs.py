#!/usr/bin/env python3
"""Generate visualizations for each run in data/runs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PARTIES = [
    "People's Party",
    "Bhumjaithai Party",
    "Pheu Thai Party",
    "Democrat Party (Thailand)",
    "Kla Tham Party",
    "Other",
]

CONDITION_LABELS = {
    "with_prior": "With prior",
    "no_prior": "No prior",
    "with_prior_social": "With prior + social",
}

CONDITION_PAIRS = [
    ("with_prior", "no_prior"),
    ("with_prior_social", "with_prior"),
]


def parse_week(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def sorted_weeks(weeks: Iterable[str]) -> List[str]:
    def key(value: str) -> Tuple[int, str]:
        parsed = parse_week(value)
        if parsed is None:
            return (1, value)
        return (0, parsed.isoformat())

    return sorted(set(weeks), key=key)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def safe_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def condition_from_filename(name: str) -> Tuple[Optional[str], Optional[str]]:
    if name.endswith(".no_prior.json"):
        return "no_prior", name[: -len(".no_prior.json")]
    if name.endswith(".with_prior_social.json"):
        return "with_prior_social", name[: -len(".with_prior_social.json")]
    if name.endswith(".json"):
        return "with_prior", name[: -len(".json")]
    return None, None


def load_forecasts(run_dir: Path) -> Dict[str, Dict[str, Dict[str, Dict[str, int]]]]:
    forecasts: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    forecast_root = run_dir / "forecasts"
    if not forecast_root.exists():
        return forecasts

    for model_dir in sorted(forecast_root.iterdir()):
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        for path in sorted(model_dir.glob("*.json")):
            condition, week_start = condition_from_filename(path.name)
            if not condition or not week_start:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            totals = data.get("forecast_total", {})
            normalized = {party: safe_int(totals.get(party)) for party in PARTIES}
            forecasts[model][condition][week_start] = normalized
    return forecasts


def plot_forecast_totals(
    out_path: Path,
    model: str,
    condition: str,
    week_order: List[str],
    totals_by_week: Dict[str, Dict[str, int]],
) -> None:
    x = list(range(len(week_order)))
    fig, ax = plt.subplots(figsize=(12, 6))
    for party in PARTIES:
        values = [totals_by_week.get(week, {}).get(party) for week in week_order]
        ax.plot(x, values, marker="o", linewidth=1.6, label=party)

    label = CONDITION_LABELS.get(condition, condition)
    ax.set_title(f"Forecast totals - {model} - {label}")
    ax.set_xlabel("Week start")
    ax.set_ylabel("Total seats")
    ax.set_xticks(x)
    ax.set_xticklabels(week_order, rotation=45, ha="right")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize="small")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_forecast_divergence(
    out_path: Path,
    model: str,
    condition_pairs: List[Tuple[str, str]],
    conditions: Dict[str, Dict[str, Dict[str, int]]],
) -> None:
    lines: Dict[str, Tuple[List[str], List[int]]] = {}

    for left, right in condition_pairs:
        if left not in conditions or right not in conditions:
            continue
        weeks = sorted_weeks(
            set(conditions[left].keys()) & set(conditions[right].keys())
        )
        if not weeks:
            continue
        distances: List[int] = []
        for week in weeks:
            total = 0
            for party in PARTIES:
                a = conditions[left][week].get(party, 0)
                b = conditions[right][week].get(party, 0)
                total += abs(a - b)
            distances.append(total)
        label = f"{CONDITION_LABELS.get(left, left)} vs {CONDITION_LABELS.get(right, right)}"
        lines[label] = (weeks, distances)

    if not lines:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    for label, (weeks, distances) in lines.items():
        x = list(range(len(weeks)))
        ax.plot(x, distances, marker="o", linewidth=1.6, label=label)
    ax.set_title(f"Condition divergence (L1 total seats) - {model}")
    ax.set_xlabel("Week start")
    ax.set_ylabel("L1 distance (seats)")
    ax.set_xticks(list(range(len(weeks))))
    ax.set_xticklabels(weeks, rotation=45, ha="right")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize="small")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_forecast_volatility(
    out_path: Path,
    model: str,
    condition: str,
    week_order: List[str],
    totals_by_week: Dict[str, Dict[str, int]],
) -> None:
    if len(week_order) < 2:
        return

    changes = {party: 0 for party in PARTIES}
    for idx in range(1, len(week_order)):
        prev_week = week_order[idx - 1]
        curr_week = week_order[idx]
        prev = totals_by_week.get(prev_week)
        curr = totals_by_week.get(curr_week)
        if not prev or not curr:
            continue
        for party in PARTIES:
            changes[party] += abs(curr.get(party, 0) - prev.get(party, 0))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = list(range(len(PARTIES)))
    values = [changes[party] for party in PARTIES]
    ax.bar(x, values, color="#4c78a8")
    ax.set_title(f"Total volatility by party - {model} - {CONDITION_LABELS.get(condition, condition)}")
    ax.set_xlabel("Party")
    ax.set_ylabel("Sum abs week-to-week change")
    ax.set_xticks(x)
    ax.set_xticklabels(PARTIES, rotation=30, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_search_summary(
    out_path: Path,
    run_label: str,
    track_label: str,
    summary_rows: List[Dict[str, str]],
) -> None:
    if not summary_rows:
        return

    weeks = sorted_weeks(row["week_start"] for row in summary_rows if row.get("week_start"))
    models = sorted(set(row.get("model", "") for row in summary_rows if row.get("model")))

    metrics = [
        ("source_count", "Sources"),
        ("unique_publishers", "Unique publishers"),
        ("query_count", "Queries"),
        ("excluded_count", "Excluded"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for idx, (metric, label) in enumerate(metrics):
        ax = axes[idx]
        for model in models:
            row_map = {row["week_start"]: row for row in summary_rows if row.get("model") == model}
            values = [safe_int(row_map.get(week, {}).get(metric)) for week in weeks]
            ax.plot(range(len(weeks)), values, marker="o", linewidth=1.4, label=model)
        ax.set_title(label)
        ax.set_xticks(range(len(weeks)))
        ax.set_xticklabels(weeks, rotation=45, ha="right")
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"Search summary - {track_label} ({run_label})", y=1.02)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(1.02, 1.02), fontsize="small")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_top_publishers(
    out_path: Path,
    run_label: str,
    track_label: str,
    publisher_rows: List[Dict[str, str]],
    top_n: int,
) -> None:
    if not publisher_rows:
        return

    counts: Counter[str] = Counter()
    for row in publisher_rows:
        publisher = row.get("publisher", "Unknown")
        counts[publisher] += safe_int(row.get("count", 0))

    if not counts:
        return

    top = counts.most_common(top_n)
    labels = [label for label, _ in reversed(top)]
    values = [value for _, value in reversed(top)]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(labels)), values, color="#f58518")
    ax.set_title(f"Top publishers - {track_label} ({run_label})")
    ax.set_xlabel("Source count")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def visualize_run(run_dir: Path, top_publishers: int) -> None:
    run_label = run_dir.name
    out_dir = run_dir / "visualizations"
    forecast_out = out_dir / "forecasts"
    search_out = out_dir / "search"
    forecast_out.mkdir(parents=True, exist_ok=True)
    search_out.mkdir(parents=True, exist_ok=True)

    forecasts = load_forecasts(run_dir)
    for model, conditions in forecasts.items():
        for condition, totals_by_week in conditions.items():
            weeks = sorted_weeks(totals_by_week.keys())
            if not weeks:
                continue
            totals_path = forecast_out / f"forecast_totals_{model}_{condition}.png"
            plot_forecast_totals(totals_path, model, condition, weeks, totals_by_week)

            vol_path = forecast_out / f"forecast_volatility_{model}_{condition}.png"
            plot_forecast_volatility(vol_path, model, condition, weeks, totals_by_week)

        divergence_path = forecast_out / f"forecast_divergence_{model}.png"
        plot_forecast_divergence(divergence_path, model, CONDITION_PAIRS, conditions)

    analysis_dir = run_dir / "analysis"
    for track in ("news", "social", "combined"):
        track_dir = analysis_dir / track
        if not track_dir.exists():
            continue

        summary_path = track_dir / "search_summary.csv"
        if summary_path.exists():
            summary_rows = read_csv_rows(summary_path)
            plot_search_summary(
                search_out / f"search_summary_{track}.png",
                run_label,
                track,
                summary_rows,
            )

        publisher_path = track_dir / "publisher_counts.csv"
        if publisher_path.exists():
            publisher_rows = read_csv_rows(publisher_path)
            plot_top_publishers(
                search_out / f"top_publishers_{track}.png",
                run_label,
                track,
                publisher_rows,
                top_publishers,
            )


def iter_runs(runs_dir: Path, run_ids: Optional[List[str]]) -> Iterable[Path]:
    if run_ids:
        for run_id in run_ids:
            path = runs_dir / run_id
            if path.is_dir():
                yield path
            else:
                print(f"Missing run: {path}")
        return
    if not runs_dir.exists():
        return
    for path in sorted(runs_dir.iterdir()):
        if path.is_dir():
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate visualizations for run outputs.")
    parser.add_argument("--runs-dir", default="data/runs", help="Root directory of runs.")
    parser.add_argument("--run-id", action="append", help="Specific run id to visualize.")
    parser.add_argument("--top-publishers", type=int, default=12, help="Top publishers to chart.")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    ran_any = False
    for run_dir in iter_runs(runs_dir, args.run_id):
        ran_any = True
        print(f"Visualizing: {run_dir}")
        visualize_run(run_dir, args.top_publishers)

    if not ran_any:
        print("No runs found to visualize.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
