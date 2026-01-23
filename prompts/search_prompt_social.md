# Weekly Social Sentiment Search Prompt (Template)

You are preparing evidence for a weekly election-forecast update using social media sentiment.

Constraints:
- Only include sources with publication dates in the range {{week_start}} to {{week_end}} inclusive.
- Timezone for date interpretation: {{timezone}}.
- If a source date is uncertain or outside the window, exclude it.
- Focus on Thai social media platforms, Thai-language posts, and sentiment analysis reports.
- Use multiple queries and include multiple sources (minimum 15 sources and at least 3 distinct platforms or publishers).

Preferred sources and keywords (use Thai when possible):
- Platforms: X (Twitter), Facebook
- Keywords: พรรคประชาชน, พรรคเพื่อไทย, พรรคภูมิใจไทย, พรรคประชาธิปัตย์, พรรคกล้าธรรม
- Add sentiment keywords: กระแส, ความนิยม, คะแนนนิยม, โพล, แฮชแท็ก, ดราม่า

Task:
1) Use your web search tools with explicit date filtering to the week window.
2) Collect 15-30 sources from that week.
3) Restrict the search to only on social media platform: X, Facebook only
4) Provide a concise sentiment summary and indicate which parties trend positive/negative/neutral.

Return JSON only in this format:
{
  "week_start": "{{week_start}}",
  "week_end": "{{week_end}}",
  "model": "{{model}}",
  "queries": [
    "..."
  ],
  "sources": [
    {
      "title": "...",
      "url": "...",
      "date": "YYYY-MM-DD",
      "publisher": "...",
      "why_relevant": "..."
    }
  ],
  "excluded_sources": [
    {
      "title": "...",
      "url": "...",
      "date": "YYYY-MM-DD or unknown",
      "publisher": "...",
      "reason": "outside window or date unclear"
    }
  ],
  "summary": [
    "...",
    "..."
  ],
  "notes": "..."
}
