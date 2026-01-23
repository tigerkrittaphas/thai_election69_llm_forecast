#!/usr/bin/env python3
"""Run weekly forecast prompt via LLM and save forecast JSON."""

import argparse
import json
from pathlib import Path

from llm_utils import call_provider, env_float, env_int, load_dotenv, render_template


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run weekly forecast prompt via LLM.")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--condition", required=True, choices=["with_prior", "no_prior"])
    parser.add_argument("--week-start", required=True)
    parser.add_argument("--week-end", required=True)
    parser.add_argument("--timezone", default="Asia/Bangkok")
    parser.add_argument("--search-log", required=True, help="Path to weekly search log JSON.")
    parser.add_argument("--prior", help="Path to prior forecast JSON (with_prior only).")
    parser.add_argument("--baseline", default="data/priors/seed_2023_reference.json")
    parser.add_argument("--prompt-with-prior", default="prompts/forecast_prompt_with_prior.md")
    parser.add_argument("--prompt-no-prior", default="prompts/forecast_prompt_no_prior.md")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    parser.add_argument("--response-json", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--allow-non-json", action="store_true")
    args = parser.parse_args()

    load_dotenv()

    search_log = load_json(Path(args.search_log))

    if args.condition == "with_prior":
        if not args.prior:
            raise SystemExit("--prior is required for with_prior.")
        prior_json = load_json(Path(args.prior))
        prompt_path = Path(args.prompt_with_prior)
        variables = {
            "week_start": args.week_start,
            "week_end": args.week_end,
            "timezone": args.timezone,
            "model": args.model,
            "search_log_json": json.dumps(search_log, ensure_ascii=False),
            "prior_json": json.dumps(prior_json, ensure_ascii=False),
        }
    else:
        baseline_json = load_json(Path(args.baseline))
        prompt_path = Path(args.prompt_no_prior)
        variables = {
            "week_start": args.week_start,
            "week_end": args.week_end,
            "timezone": args.timezone,
            "model": args.model,
            "search_log_json": json.dumps(search_log, ensure_ascii=False),
            "baseline_json": json.dumps(baseline_json, ensure_ascii=False),
        }

    template = load_text(prompt_path)
    rendered = render_template(template, variables)

    if args.temperature == 0.0:
        args.temperature = env_float("DEFAULT_TEMPERATURE", args.temperature)
    if args.timeout == 60:
        args.timeout = env_int("LLM_TIMEOUT", args.timeout)

    response = call_provider(
        args.provider,
        rendered,
        args.model,
        response_json=args.response_json,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        if not args.allow_non_json:
            raise SystemExit("Model response is not valid JSON. Re-run or pass --allow-non-json.")
        out_path.write_text(response, encoding="utf-8")
        return 0

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
