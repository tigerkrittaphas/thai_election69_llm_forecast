#!/usr/bin/env bash
set -euo pipefail

prev_week_start=""
total_weeks=$(awk 'NR>1 {count++} END {print count+0}' data/weeks.csv)
current_week=0
run_id="${RUN_ID:-$(date +%Y%m%d_%H%M%S)_$$}"
run_dir="${RUN_DIR:-data/runs/$run_id}"

mkdir -p "$run_dir"
echo "Run dir: $run_dir"

progress_bar() {
  local current=$1
  local total=$2
  local width=30
  local filled=$((current * width / total))
  local empty=$((width - filled))
  local bar
  local space
  bar=$(printf "%*s" "$filled" "" | tr ' ' '#')
  space=$(printf "%*s" "$empty" "")
  printf "\rProgress: [%s%s] %d/%d" "$bar" "$space" "$current" "$total"
}

pick_prior() {
  local candidate
  for candidate in "$@"; do
    if [ -f "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 0
}

while IFS=, read -r week_index week_start week_end; do
  if [ "$week_index" = "week_index" ]; then
    continue
  fi

  current_week=$((current_week + 1))
  progress_bar "$current_week" "$total_weeks"
  echo " Week $current_week/$total_weeks: $week_start to $week_end"

  # for model in gpt-5.2 gemini-3-pro claude-opus-4.5; do
  for model in gpt-5.2; do
    echo "  Model: $model"
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
      gpt-5-mini)
        provider="openai"
        search_flag=""
        ;;
    esac

    search_log="$run_dir/search_logs/$model/$week_start.json"
    echo "    Search (news) -> $search_log"
    ./scripts/run_search_llm.py \
      --provider "$provider" \
      --model "$model" \
      --week-start "$week_start" \
      --week-end "$week_end" \
      --out "$search_log" \
      $search_flag \
      --response-json

    search_log_social="$run_dir/search_logs_social/$model/$week_start.json"
    echo "    Search (social) -> $search_log_social"
    ./scripts/run_search_llm.py \
      --provider "$provider" \
      --model "$model" \
      --week-start "$week_start" \
      --week-end "$week_end" \
      --prompt-file prompts/search_prompt_social.md \
      --out "$search_log_social" \
      $search_flag \
      --response-json

    no_prior_out="$run_dir/forecasts/$model/$week_start.no_prior.json"
    echo "    Forecast (no prior) -> $no_prior_out"
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
      prior_with="$run_dir/forecasts/$model/$prev_week_start.json"
      prior_no="$run_dir/forecasts/$model/$prev_week_start.no_prior.json"
      prior_social="$run_dir/forecasts/$model/$prev_week_start.with_prior_social.json"

      prior_file="$(pick_prior "$prior_with" "$prior_no")"
      if [ -n "$prior_file" ]; then
        with_prior_out="$run_dir/forecasts/$model/$week_start.json"
        echo "    Forecast (with prior; prior=$prior_file) -> $with_prior_out"
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
      else
        echo "    Forecast (with prior) skipped: no prior file."
      fi

      social_prior_file="$(pick_prior "$prior_social" "$prior_with" "$prior_no")"
      if [ -n "$social_prior_file" ]; then
        with_prior_social_out="$run_dir/forecasts/$model/$week_start.with_prior_social.json"
        echo "    Forecast (with prior + social; prior=$social_prior_file) -> $with_prior_social_out"
        ./scripts/run_forecast_llm.py \
          --provider "$provider" \
          --model "$model" \
          --condition with_prior \
          --week-start "$week_start" \
          --week-end "$week_end" \
          --search-log "$search_log_social" \
          --prior "$social_prior_file" \
          --out "$with_prior_social_out" \
          --response-json
      else
        echo "    Forecast (with prior + social) skipped: no prior file."
      fi
    fi
  done

  prev_week_start="$week_start"
done < data/weeks.csv

progress_bar "$total_weeks" "$total_weeks"
echo ""

./scripts/analyze_search_logs.py "$run_dir/search_logs" --out-dir "$run_dir/analysis/news"
./scripts/analyze_search_logs.py "$run_dir/search_logs_social" --out-dir "$run_dir/analysis/social"
./scripts/analyze_search_logs.py "$run_dir/search_logs" "$run_dir/search_logs_social" --out-dir "$run_dir/analysis/combined"
