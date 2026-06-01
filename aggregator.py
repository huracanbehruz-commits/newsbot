import asyncio
from tg_reader import fetch_telegram
from web_scraper import fetch_rss

TOPIC_HEADERS = {
    "investment": "💰 *INVESTMENT NEWS*",
    "startup":    "🚀 *STARTUP & FOUNDER INFO*",
    "insights":   "🧠 *PROFESSIONAL INSIGHTS*",
    "breakdown":  "🏢 *COMPANY & TECH BREAKDOWNS*",
}

REGION_LABELS = {
    "uz":    "🇺🇿 Uzbekistan",
    "ca":    "🌏 Central Asia",
    "world": "🌍 Worldwide",
}

SOURCE_EMOJI = {
    "telegram": "✈️",
    "rss":      "🌐",
}

TEMPLATES = {
    "investment": "💰 *{title}*\n📝 {description}\n🔗 [Open]({url}) · _{source}_",
    "startup":    "🚀 *{title}*\n📝 {description}\n🔗 [Open]({url}) · _{source}_",
    "insights":   "🧠 *{title}*\n📝 {description}\n🔗 [Open]({url}) · _{source}_",
    "breakdown":  "🏢 *{title}*\n📝 {description}\n🔗 [Open]({url}) · _{source}_",
}


class NewsAggregator:
    def __init__(self, tg_api_id: int, tg_api_hash: str, tg_session_str: str = ""):
        self.tg_api_id      = tg_api_id
        self.tg_api_hash    = tg_api_hash
        self.tg_session_str = tg_session_str

    async def fetch_all(self, topic: str, region: str) -> list[dict]:
        tg_result, rss_result = await asyncio.gather(
            asyncio.wait_for(
                fetch_telegram(topic, region, self.tg_api_id, self.tg_api_hash, self.tg_session_str),
                timeout=15
            ),
            asyncio.wait_for(fetch_rss(topic, region), timeout=10),
            return_exceptions=True
        )

        tg_articles  = tg_result  if isinstance(tg_result,  list) else []
        rss_articles = rss_result if isinstance(rss_result, list) else []

        # Telegram posts sorted by date (newest first)
        tg_articles.sort(key=lambda x: x.get("date") or "", reverse=True)

        # Combine: Telegram first, then RSS
        combined = tg_articles + rss_articles

        # Deduplicate by title
        seen, unique = set(), []
        for a in combined:
            key = a["title"].lower()[:60]
            if key not in seen:
                seen.add(key)
                unique.append(a)

        return unique[:5]  # Top 5 only

    def format(self, articles: list[dict], topic: str, region: str) -> str:
        header   = f"{TOPIC_HEADERS[topic]} · {REGION_LABELS[region]}"
        template = TEMPLATES[topic]
        divider  = "─" * 28
        lines    = [header, ""]

        for i, a in enumerate(articles, 1):
            desc = (a.get("description") or "").strip()
            if not desc:
                desc = "No description available."
            if len(desc) > 250:
                desc = desc[:247] + "..."

            emoji  = SOURCE_EMOJI.get(a.get("origin", "rss"), "🌐")
            source = f"{emoji} {a['source']}"
            card   = template.format(
                title=a["title"],
                description=desc,
                url=a["url"],
                source=source,
            )
            lines.append(f"*{i}.* {card}")
            if i < len(articles):
                lines.append(divider)

        return "\n".join(lines)
