# Weekly News Search Prompt (Template)

You are preparing evidence for a weekly election-forecast update.

Constraints:
- Only include sources with publication dates in the range {{week_start}} to {{week_end}} inclusive.
- Timezone for date interpretation: {{timezone}}.
- If a source date is uncertain or outside the window, exclude it.
- Prefer Thai-language and Thai-local news sources when available.
- Focus on Thai politics, polling, party dynamics, endorsements, scandals, legal actions, or coalition signals.
- Use multiple queries and include multiple sources (minimum 15 sources and at least 3 distinct publishers).

Suggested Thai queries (use Thai keywords when possible):
- การเลือกตั้ง 2566/2567/2568/2569 ข่าวการเมืองไทย
- พรรคประชาชน, พรรคเพื่อไทย, พรรคภูมิใจไทย, พรรคประชาธิปัตย์, พรรคกล้าธรรม
- โพลเลือกตั้ง, คะแนนนิยม, กระแสพรรค

Task:
1) Use your web search tools with explicit date filtering to the week window.
2) Collect 5-15 sources from that week.
3) Provide a concise evidence summary.

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
