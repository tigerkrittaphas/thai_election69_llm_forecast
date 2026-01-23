# Thai 2026 Election Simulation Study

This repository contains the protocol, prompts, and scaffolding for a weekly LLM-based simulation of Thai 2026 parliamentary seats (500 total; 100 party-list, 400 district).

## What is included
- Study protocol: `docs/study_protocol.md`
- Configuration: `config/study.yml`
- 2023 reference baseline: `data/priors/seed_2023_reference.json`
- Prompt templates: `prompts/`
- Forecast JSON schema: `schema/forecast_schema.json`
- Search log JSON schema: `schema/search_log_schema.json`
- Helper scripts: `scripts/`
- Env template: `.env.example`

## Quickstart
1) Generate weekly windows:
```
./scripts/generate_weeks.py --out data/weeks.csv
```

2) For each week and model, run two conditions:
- with prior (`prompts/forecast_prompt_with_prior.md`)
- no prior (`prompts/forecast_prompt_no_prior.md`)

3) Store outputs at (set `RUN_ID` or `RUN_DIR` to control the run folder; default uses a timestamp):
`data/runs/{run_id}/forecasts/{model}/{week_start}.json`
and search logs at:
`data/runs/{run_id}/search_logs/{model}/{week_start}.json`

4) Validate outputs:
```
./scripts/validate_forecast.py data/runs/{run_id}/forecasts
```

5) Analyze search logs:
```
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs --out-dir data/runs/{run_id}/analysis/news
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs_social --out-dir data/runs/{run_id}/analysis/social
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs data/runs/{run_id}/search_logs_social --out-dir data/runs/{run_id}/analysis/combined
```

## LLM API scripts
Install SDKs:
```
pip install openai anthropic google-genai
```

Set credentials in `.env` (see `.env.example`). Then call the providers directly:

Search log (per model, per week):
```
./scripts/run_search_llm.py --provider openai --model gpt-5.2 --week-start 2025-12-12 --week-end 2025-12-18 --out data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json --enable-search-tool --response-json
```

Note: the Anthropic SDK does not include built-in web search; use another provider for search or integrate an external search tool.

Social sentiment search (optional track):
```
./scripts/run_search_llm.py --provider openai --model gpt-5.2 --week-start 2025-12-12 --week-end 2025-12-18 --prompt-file prompts/search_prompt_social.md --out data/runs/{run_id}/search_logs_social/gpt-5.2/2025-12-12.json --enable-search-tool --response-json
```

## Run the full experiment (bash)
This loops over `data/weeks.csv`, runs search logs and forecasts for each model, and then builds search log analysis.

```bash
#!/usr/bin/env bash
set -euo pipefail

prev_week_start=""
run_id="${RUN_ID:-2026-01-21}"
run_dir="${RUN_DIR:-data/runs/$run_id}"

while IFS=, read -r week_index week_start week_end; do
  if [ "$week_index" = "week_index" ]; then
    continue
  fi

  for model in gpt-5.2 gemini-3-pro claude-opus-4.5; do
    case "$model" in
      gpt-5.2)
        provider="openai"
        search_flag="--enable-search-tool"
        ;;
      gemini-3-pro)
        provider="gemini"
        search_flag="--enable-search-tool"
        ;;
      claude-opus-4.5)
        provider="anthropic"
        search_flag=""
        ;;
    esac

    search_log="$run_dir/search_logs/$model/$week_start.json"
    ./scripts/run_search_llm.py \
      --provider "$provider" \
      --model "$model" \
      --week-start "$week_start" \
      --week-end "$week_end" \
      --out "$search_log" \
      $search_flag \
      --response-json

    no_prior_out="$run_dir/forecasts/$model/$week_start.no_prior.json"
    ./scripts/run_forecast_llm.py \
      --provider "$provider" \
      --model "$model" \
      --condition no_prior \
      --week-start "$week_start" \
      --week-end "$week_end" \
      --search-log "$search_log" \
      --out "$no_prior_out" \
      --response-json

    if [ -n "$prev_week_start" ]; then
      prior_file="$run_dir/forecasts/$model/$prev_week_start.json"
      if [ -f "$prior_file" ]; then
        with_prior_out="$run_dir/forecasts/$model/$week_start.json"
        ./scripts/run_forecast_llm.py \
          --provider "$provider" \
          --model "$model" \
          --condition with_prior \
          --week-start "$week_start" \
          --week-end "$week_end" \
          --search-log "$search_log" \
          --prior "$prior_file" \
          --out "$with_prior_out" \
          --response-json
      fi
    fi
  done

  prev_week_start="$week_start"
done < data/weeks.csv

./scripts/analyze_search_logs.py "$run_dir/search_logs" --out-dir "$run_dir/analysis/news"
./scripts/analyze_search_logs.py "$run_dir/search_logs_social" --out-dir "$run_dir/analysis/social"
./scripts/analyze_search_logs.py "$run_dir/search_logs" "$run_dir/search_logs_social" --out-dir "$run_dir/analysis/combined"
```

Forecast (with prior):
```
./scripts/run_forecast_llm.py --provider openai --model gpt-5.2 --condition with_prior --week-start 2025-12-12 --week-end 2025-12-18 --search-log data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json --prior data/runs/{run_id}/forecasts/gpt-5.2/2025-12-05.json --out data/runs/{run_id}/forecasts/gpt-5.2/2025-12-12.json --response-json
```

Forecast (no prior):
```
./scripts/run_forecast_llm.py --provider openai --model gpt-5.2 --condition no_prior --week-start 2025-12-12 --week-end 2025-12-18 --search-log data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json --out data/runs/{run_id}/forecasts/gpt-5.2/2025-12-12.no_prior.json --response-json
```

## Weekly workflow (per model)
1) Use `prompts/search_prompt.md` with the week window to collect sources (minimum 15, at least 3 publishers).
2) Summarize evidence from that week only.
3) Run forecasts:
   - Condition A: use last week's forecast as prior.
   - Condition B: use 2023 reference baseline, no prior.
4) Save JSON output and sources for reproducibility.

## Search log analysis
Use `scripts/analyze_search_logs.py` to summarize source coverage:
- sources per week and per model
- unique publishers per week
- duplicate URLs across models

## Visualizations
Generate charts for each run (forecasts and search summaries):
```
./scripts/visualize_runs.py --runs-dir data/runs
```

Single run:
```
./scripts/visualize_runs.py --run-id 20260122_212015_8539
```

Outputs are saved under:
`data/runs/{run_id}/visualizations/`

## Sensitivity analysis
Compare the two conditions over time:
- Volatility per party
- Week-to-week change magnitude
- Divergence between conditions

## Notes on baseline mapping
The 2023 reference baseline maps:
- People's Party <- Move Forward Party (successor after dissolution)
- Bhumjaithai Party <- Bhumjaithai Party
- Democrat Party (Thailand) <- Democrat Party (Thailand)
- Kla Tham Party <- not in 2023 results
- Other <- all remaining parties

See `data/priors/seed_2023_reference.json` for details.
