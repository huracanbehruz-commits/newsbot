from telethon import TelegramClient
from telethon.sessions import StringSession

# All channels tagged by region
TG_CHANNELS = [
    # Uzbekistan
    {"username": "yoshlarventures",      "region": "uz"},
    {"username": "uzcombinator",         "region": "uz"},
    {"username": "aloqaventures",        "region": "uz"},
    {"username": "mlc_uz",               "region": "uz"},
    # Central Asia
    {"username": "stanbasetech",         "region": "ca"},
    {"username": "thetechkz",            "region": "ca"},
    {"username": "digitalbussinesskz",   "region": "ca"},
    # Worldwide / general
    {"username": "startupslezamneverit", "region": "world"},
    {"username": "founderdotio",         "region": "world"},
]

REGION_INCLUDES = {
    "uz":    {"uz"},
    "ca":    {"uz", "ca"},
    "world": {"uz", "ca", "world"},
}

# Keywords in English AND Russian
TOPIC_KEYWORDS = {
    "investment": [
        # EN
        "invest", "funding", "venture", "capital", "ipo", "series a", "series b",
        "raise", "round", "acquisition", "grant", "fdi", "fund", "deal",
        # RU
        "инвест", "финансиров", "раунд", "грант", "сделк", "фонд",
        "привлек", "капитал", "венчур", "инвестор",
        # UZ
        "investitsiya", "moliyalashtirish", "grant",
    ],
    "startup": [
        # EN
        "startup", "founder", "entrepreneur", "launch", "seed", "pitch",
        "incubator", "accelerator", "founded", "co-founder",
        # RU
        "стартап", "основател", "запуск", "питч", "акселератор",
        "инкубатор", "предпринимател", "основал", "команда",
        # UZ
        "startap", "tadbirkor", "akselerator",
    ],
    "insights": [
        # EN
        "strategy", "insight", "trend", "analysis", "economy", "market",
        "growth", "forecast", "reform", "lesson", "tip", "advice",
        # RU
        "стратег", "тренд", "анализ", "рынок", "экономик", "рост",
        "реформ", "урок", "совет", "прогноз", "развити",
        # UZ
        "strategiya", "tahlil", "bozor", "rivojlanish",
    ],
    "breakdown": [
        # EN
        "fintech", "banking", "infrastructure", "platform", "technology",
        "digital", "ai", "saas", "how", "breakdown", "explained", "model",
        # RU
        "финтех", "банк", "цифров", "технолог", "платформ", "искусственн",
        "модел", "инфраструктур", "объяснен", "разбор",
        # UZ
        "texnologiya", "raqamli", "platforma",
    ],
}

_client = None


async def _get_client(api_id: int, api_hash: str, session_str: str = "") -> TelegramClient:
    global _client
    if _client and _client.is_connected():
        return _client
    if session_str:
        _client = TelegramClient(StringSession(session_str), api_id, api_hash)
    else:
        _client = TelegramClient("tg_session", api_id, api_hash)
    await _client.start()
    return _client


async def fetch_telegram(topic: str, region: str, api_id: int, api_hash: str, session_str: str = "", limit: int = 30) -> list[dict]:
    if not api_id or not api_hash:
        return []

    allowed = REGION_INCLUDES.get(region, {"world"})
    channels = [c for c in TG_CHANNELS if c["region"] in allowed]
    topic_kws = TOPIC_KEYWORDS.get(topic, [])
    articles = []

    try:
        client = await _get_client(api_id, api_hash, session_str)
        for ch in channels:
            try:
                entity   = await client.get_entity(ch["username"])
                messages = await client.get_messages(entity, limit=limit)
                for msg in messages:
                    if not msg.text:
                        continue
                    text_lower = msg.text.lower()
                    if not any(kw in text_lower for kw in topic_kws):
                        continue
                    lines = [l.strip() for l in msg.text.split("\n") if l.strip()]
                    title = lines[0][:120] if lines else msg.text[:120]
                    desc  = " ".join(lines[1:4])[:300] if len(lines) > 1 else ""
                    articles.append({
                        "title":     title,
                        "description": desc,
                        "url":       f"https://t.me/{ch['username']}/{msg.id}",
                        "source":    f"@{ch['username']}",
                        "published": msg.date.isoformat() if msg.date else "",
                        "origin":    "telegram",
                        "date":      msg.date,
                    })
            except Exception as e:
                print(f"TG error @{ch['username']}: {e}")
    except Exception as e:
        print(f"Telethon error: {e}")

    return articles
