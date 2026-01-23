#!/usr/bin/env python3
"""Call an LLM provider with a prompt template."""

import argparse
import json
import sys
from pathlib import Path

from llm_utils import call_provider, env_float, env_int, load_dotenv, render_template


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_vars(items) -> dict:
    values = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Invalid --var '{item}', expected key=value.")
        key, value = item.split("=", 1)
        values[key] = value
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Call LLM provider with a prompt template.")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", help="Path to prompt template file.")
    parser.add_argument("--prompt", help="Raw prompt string.")
    parser.add_argument("--system-file", help="Optional system prompt file.")
    parser.add_argument("--var", action="append", help="Template variable key=value.")
    parser.add_argument("--out", help="Output file path. Default: stdout.")
    parser.add_argument("--response-json", action="store_true", help="Request JSON output if supported.")
    parser.add_argument("--enable-search-tool", action="store_true", help="Enable provider web search tool.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    if not args.prompt_file and not args.prompt:
        raise SystemExit("Provide --prompt-file or --prompt.")

    load_dotenv()

    prompt_text = args.prompt or load_text(Path(args.prompt_file))
    variables = parse_vars(args.var)
    prompt_text = render_template(prompt_text, variables)

    system_text = None
    if args.system_file:
        system_text = load_text(Path(args.system_file))

    if args.temperature == 0.0:
        args.temperature = env_float("DEFAULT_TEMPERATURE", args.temperature)
    if args.timeout == 60:
        args.timeout = env_int("LLM_TIMEOUT", args.timeout)

    response = call_provider(
        args.provider,
        prompt_text,
        args.model,
        system=system_text,
        response_json=args.response_json,
        enable_search_tool=args.enable_search_tool,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )

    if args.out:
        Path(args.out).write_text(response, encoding="utf-8")
    else:
        sys.stdout.write(response)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
