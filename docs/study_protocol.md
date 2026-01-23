# Thai 2026 Election Simulation Study Protocol

Version: 0.1
Date: 2026-01-21

## 1) Objective
Run weekly, model-based simulations of the 2026 Thai general election to forecast the distribution of 500 seats across major parties, with a sensitivity analysis on the use of prior-week predictions.

## 2) Electoral system
- Total seats: 500
- Party-list seats: 100
- District seats: 400
- Voting system: parallel voting (separate ballots for party-list and district)

## 3) Parties tracked
Forecasts must include these categories and sum to 500 total seats:
- People's Party
- Bhumjaithai Party
- Pheu Thai Party
- Democrat Party (Thailand)
- Kla Tham Party
- Other (all remaining parties combined)

## 4) Models
Each model runs weekly forecasts with default reasoning settings:
- GPT-5.2
- Gemini-3-pro
- Claude Opus 4.5

## 5) Timeframe and cadence
- Weekly rounds starting 2025-12-12, continuing through the present.
- Week window: 7 days, inclusive.
- Timezone: Asia/Bangkok.

## 6) Data sources and search constraints
- Each model uses its own web search tools to gather sources only from the defined week window.
- Only include sources dated within the week window (inclusive).
- Search must include multiple sources each week (minimum 15, at least 3 distinct publishers).
- Prefer Thai-language and Thai-local sources when available.
- Log queries plus all URLs, titles, publishers, and publication dates per week.
- Store search logs for later analysis.

## 7) Forecast tasks per week
For each model and each week:
1) Search: gather sources from that week only and log queries + results.
2) Evidence summary: brief bullet summary of relevant signals.
3) Forecast: produce party-list and district seat distributions.
4) Validation: enforce integer seats, no negatives, correct totals.
5) Storage: save forecast, search log, and rationale.

## 8) Search log analysis
Analyze weekly search logs for source diversity and coverage. Run separate analyses for news-only, social-only, and combined sources:
- Number of sources per week and per model
- Unique publishers per week
- Duplicate sources across models
- Changes in publisher mix over time

## 8a) Alternate evidence track: social sentiment
Run a parallel weekly search that focuses on social media sentiment using a dedicated prompt template. Results are stored separately and can be used for a sentiment-driven forecast condition.

## 9) Prior use and sensitivity analysis
Two conditions run in parallel each week:
- Condition A (with prior): use last week's model forecast as a prior, then adjust using current week evidence.
- Condition B (no prior): ignore all prior-week forecasts. Use the 2023 reference baseline and adjust only with current week evidence.

Compare the two conditions on:
- Total-seat shifts week over week
- Volatility per party (std dev over time)
- Divergence between conditions (e.g., L1 distance)

## 10) Baseline reference (2023)
The initial baseline uses 2023 election results as a reference point, mapped to the study parties. This is a reference only and not an assumption of 2026 outcomes.
- People's Party is treated as the successor to the dissolved Move Forward Party for mapping purposes
- Bhumjaithai Party is mapped from the 2023 Bhumjaithai Party
- Democrat Party (Thailand) is mapped from the 2023 Democrat Party (Thailand)
- Kla Tham Party does not appear in the 2023 results
- Other includes all remaining parties

Reference source:
- https://en.wikipedia.org/wiki/2023_Thai_general_election

## 11) Output format
Each forecast must include totals and splits:
- Party-list seats (sum to 100)
- District seats (sum to 400)
- Total seats (sum to 500)

JSON schemas are defined in:
- `schema/forecast_schema.json`
- `schema/search_log_schema.json`

## 12) Storage layout
- Config: `config/study.yml`
- Baseline prior: `data/priors/seed_2023_reference.json`
- Runs root: `data/runs/{run_id}/`
- Forecasts: `data/runs/{run_id}/forecasts/{model}/{week_start}.json`
- Search logs: `data/runs/{run_id}/search_logs/{model}/{week_start}.json`
- Weeks index: `data/weeks.csv`
- Prompt templates: `prompts/`
- Analysis outputs: `data/runs/{run_id}/analysis/`

## 13) Limitations
- News coverage is uneven; weekly evidence may be sparse.
- Party realignments between 2023 and 2026 are expected; baseline is only a reference.
- LLM outputs are not predictions of real election outcomes.
