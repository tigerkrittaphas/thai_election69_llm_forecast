# Weekly Forecast Prompt (No Prior)

You are forecasting the weekly distribution of 500 Thai parliamentary seats.

Inputs you will receive:
- Week window: {{week_start}} to {{week_end}} (timezone {{timezone}})
- Sources + summary from that week
- 2023 reference baseline (mapped to study parties)

Search log JSON (from this week):
{{search_log_json}}

2023 baseline JSON:
{{baseline_json}}

Constraints:
- Use only sources dated within the week window.
- Do NOT use any previous weekly forecasts.
- Use the 2023 reference baseline as the starting point each week.
- Produce integer seat counts.
- Party-list seats must sum to 100; district seats must sum to 400; total must sum to 500.
- Parties: People's Party, Bhumjaithai Party, Pheu Thai Party, Democrat Party (Thailand), Kla Tham Party, Other.

Return JSON only in this format:
{
  "week_start": "{{week_start}}",
  "week_end": "{{week_end}}",
  "model": "{{model}}",
  "condition": "no_prior",
  "baseline": "2023_reference",
  "forecast_party_list": {
    "People's Party": 0,
    "Bhumjaithai Party": 0,
    "Pheu Thai Party": 0,
    "Democrat Party (Thailand)": 0,
    "Kla Tham Party": 0,
    "Other": 0
  },
  "forecast_district": {
    "People's Party": 0,
    "Bhumjaithai Party": 0,
    "Pheu Thai Party": 0,
    "Democrat Party (Thailand)": 0,
    "Kla Tham Party": 0,
    "Other": 0
  },
  "forecast_total": {
    "People's Party": 0,
    "Bhumjaithai Party": 0,
    "Pheu Thai Party": 0,
    "Democrat Party (Thailand)": 0,
    "Kla Tham Party": 0,
    "Other": 0
  },
  "rationale": [
    "..."
  ],
  "checks": {
    "party_list_sum": 100,
    "district_sum": 400,
    "total_sum": 500
  }
}
