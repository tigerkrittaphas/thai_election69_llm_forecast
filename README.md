# Thai 2026 Election Simulation Study

A reproducible, weekly LLM-based simulation of Thailand’s 2026 parliamentary election seat distribution (500 total seats: 100 party‑list, 400 district). The repository contains the protocol, prompts, schemas, and scripts needed to generate, validate, and visualize forecasts across models and conditions.

## What’s inside
- Study protocol: `docs/study_protocol.md`
- Configuration: `config/study.yml`
- 2023 reference baseline: `data/priors/seed_2023_reference.json`
- Prompt templates: `prompts/`
- JSON schemas: `schema/forecast_schema.json`, `schema/search_log_schema.json`
- Helper scripts: `scripts/`
- Runs and outputs: `data/runs/`

## Core ideas
- Weekly evidence windows (7 days, Asia/Bangkok time).
- Two conditions per model:
  - **With prior**: update from last week’s forecast.
  - **No prior**: update from the 2023 reference baseline only.
- Search logs are recorded and analyzed for source coverage and diversity.

## Quickstart
Generate weekly windows:
```bash
./scripts/generate_weeks.py --out data/weeks.csv
```

Run a single week (example, with search logs):
```bash
./scripts/run_search_llm.py --provider openai --model gpt-5.2 \
  --week-start 2025-12-12 --week-end 2025-12-18 \
  --out data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json \
  --enable-search-tool --response-json
```

Forecast (with prior):
```bash
./scripts/run_forecast_llm.py --provider openai --model gpt-5.2 \
  --condition with_prior --week-start 2025-12-12 --week-end 2025-12-18 \
  --search-log data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json \
  --prior data/runs/{run_id}/forecasts/gpt-5.2/2025-12-05.json \
  --out data/runs/{run_id}/forecasts/gpt-5.2/2025-12-12.json \
  --response-json
```

Forecast (no prior):
```bash
./scripts/run_forecast_llm.py --provider openai --model gpt-5.2 \
  --condition no_prior --week-start 2025-12-12 --week-end 2025-12-18 \
  --search-log data/runs/{run_id}/search_logs/gpt-5.2/2025-12-12.json \
  --out data/runs/{run_id}/forecasts/gpt-5.2/2025-12-12.no_prior.json \
  --response-json
```

Validate outputs:
```bash
./scripts/validate_forecast.py data/runs/{run_id}/forecasts
```

Analyze search logs:
```bash
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs --out-dir data/runs/{run_id}/analysis/news
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs_social --out-dir data/runs/{run_id}/analysis/social
./scripts/analyze_search_logs.py data/runs/{run_id}/search_logs data/runs/{run_id}/search_logs_social --out-dir data/runs/{run_id}/analysis/combined
```

Visualize results:
```bash
./scripts/visualize_runs.py --runs-dir data/runs
# or a single run
./scripts/visualize_runs.py --run-id 20260122_212015_8539
```

## Full run loop (bash)
This loops across `data/weeks.csv`, runs search logs and forecasts for each model, and builds search‑log analysis.

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

## Storage layout
- Config: `config/study.yml`
- Baseline prior: `data/priors/seed_2023_reference.json`
- Runs root: `data/runs/{run_id}/`
- Forecasts: `data/runs/{run_id}/forecasts/{model}/{week_start}.json`
- Search logs: `data/runs/{run_id}/search_logs/{model}/{week_start}.json`
- Weeks index: `data/weeks.csv`
- Analysis outputs: `data/runs/{run_id}/analysis/`

## Notes on baseline mapping
The 2023 reference baseline maps:
- People’s Party ← Move Forward Party (successor after dissolution)
- Bhumjaithai Party ← Bhumjaithai Party
- Democrat Party (Thailand) ← Democrat Party (Thailand)
- Kla Tham Party ← not in 2023 results
- Other ← all remaining parties

See `data/priors/seed_2023_reference.json` for details.

## Limitations
- News coverage is uneven; weekly evidence may be sparse.
- Party realignments between 2023 and 2026 are expected; baseline is only a reference.
- LLM outputs are not predictions of real election outcomes.
