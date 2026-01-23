# Weekly Forecast Prompt (With Prior)

You are forecasting the weekly distribution of 500 Thai parliamentary seats.

Inputs you will receive:
- Week window: {{week_start}} to {{week_end}} (timezone {{timezone}})
- Sources + summary from that week
- Prior forecast from the previous week (same model)

Search log JSON (from this week):
{{search_log_json}}

Prior forecast JSON (previous week, same model):
{{prior_json}}

Constraints:
- Use only sources dated within the week window.
- Use the prior forecast as your starting point.
- Produce integer seat counts.
- Party-list seats must sum to 100; district seats must sum to 400; total must sum to 500.
- Parties: People's Party, Bhumjaithai Party, Pheu Thai Party, Democrat Party (Thailand), Kla Tham Party, Other.

Return JSON only in this format:
{
  "week_start": "{{week_start}}",
  "week_end": "{{week_end}}",
  "model": "{{model}}",
  "condition": "with_prior",
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
  "delta_from_prior_total": {
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
