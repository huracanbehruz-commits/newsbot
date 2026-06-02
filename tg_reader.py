from telethon import TelegramClient
from telethon.sessions import StringSession

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

TOPIC_KEYWORDS = {
    "investment": [
        "invest", "funding", "venture", "capital", "ipo", "series a", "series b",
        "raise", "round", "acquisition", "grant", "fdi", "fund", "deal",
        "инвест", "финансиров", "раунд", "грант", "сделк", "фонд",
        "привлек", "капитал", "венчур", "инвестор",
        "investitsiya", "moliyalashtirish",
    ],
    "startup": [
        "startup", "founder", "entrepreneur", "launch", "seed", "pitch",
        "incubator", "accelerator", "founded", "co-founder",
        "стартап", "основател", "запуск", "питч", "акселератор",
        "инкубатор", "предпринимател", "основал",
        "startap", "tadbirkor", "akselerator",
    ],
    "insights": [
        "strategy", "insight", "trend", "analysis", "economy", "market",
        "growth", "forecast", "reform", "lesson", "tip", "advice",
        "стратег", "тренд", "анализ", "рынок", "экономик", "рост",
        "реформ", "урок", "совет", "прогноз",
        "strategiya", "tahlil", "bozor",
    ],
    "breakdown": [
        "fintech", "banking", "infrastructure", "platform", "technology",
        "digital", "ai", "saas", "how", "breakdown", "explained", "model",
        "финтех", "банк", "цифров", "технолог", "платформ",
        "инфраструктур", "разбор",
        "texnologiya", "raqamli", "platforma",
    ],
}

_client = None


async def _get_client(api_id: int, api_hash: str, session_str: str) -> TelegramClient:
    global _client
    if _client and _client.is_connected():
        return _client

    # Always use StringSession — never fall back to bot token
    session = StringSession(session_str) if session_str else StringSession()
    _client = TelegramClient(session, api_id, api_hash)

    # connect() only — do NOT call start() which can trigger bot token auth
    await _client.connect()

    if not await _client.is_user_authorized():
        raise RuntimeError("TG_SESSION_STR is missing or invalid. Generate it locally first.")

    return _client


async def fetch_telegram(topic: str, region: str, api_id: int, api_hash: str, session_str: str = "", limit: int = 30) -> list[dict]:
    if not api_id or not api_hash or not session_str:
        print("Skipping Telegram: missing credentials")
        return []

    allowed   = REGION_INCLUDES.get(region, {"world"})
    channels  = [c for c in TG_CHANNELS if c["region"] in allowed]
    topic_kws = TOPIC_KEYWORDS.get(topic, [])
    articles  = []

    try:
        client = await _get_client(api_id, api_hash, session_str)

        for ch in channels:
            try:
                entity   = await client.get_entity(ch["username"])
                messages = await client.get_messages(entity, limit=limit)
                for msg in messages:
                    if not msg.text:
                        continue
                    if not any(kw in msg.text.lower() for kw in topic_kws):
                        continue
                    lines = [l.strip() for l in msg.text.split("\n") if l.strip()]
                    title = lines[0][:120] if lines else msg.text[:120]
                    desc  = " ".join(lines[1:4])[:300] if len(lines) > 1 else ""
                    articles.append({
                        "title":       title,
                        "description": desc,
                        "url":         f"https://t.me/{ch['username']}/{msg.id}",
                        "source":      f"@{ch['username']}",
                        "published":   msg.date.isoformat() if msg.date else "",
                        "origin":      "telegram",
                        "date":        msg.date,
                    })
            except Exception as e:
                print(f"TG error @{ch['username']}: {e}")

    except Exception as e:
        print(f"Telethon error: {e}")

    return articles
