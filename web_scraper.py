import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup

RSS_SOURCES = [
    # Uzbekistan
    {"url": "https://it-park.uz/uz/itpark/news/rss",  "name": "IT Park UZ",         "region": "uz"},
    {"url": "https://digital.uz/rss/",                "name": "Digital UZ",          "region": "uz"},
    {"url": "https://kun.uz/en/rss",                  "name": "Kun.uz",              "region": "uz"},
    {"url": "https://www.gazeta.uz/en/rss/",          "name": "Gazeta.uz",           "region": "uz"},
    {"url": "https://www.fwdstart.me/rss",            "name": "FwdStart",            "region": "uz"},
    # Central Asia
    {"url": "https://digitalbusiness.kz/feed/",       "name": "Digital Business KZ", "region": "ca"},
    {"url": "https://the-tech.kz/feed/",              "name": "The Tech KZ",         "region": "ca"},
    {"url": "https://wamda.com/feed",                 "name": "Wamda",               "region": "ca"},
    # Worldwide startup/tech
    {"url": "https://www.eu-startups.com/feed/",      "name": "EU Startups",         "region": "world"},
    {"url": "https://sifted.eu/feed",                 "name": "Sifted",              "region": "world"},
    {"url": "https://techcrunch.com/feed/",           "name": "TechCrunch",          "region": "world"},
    {"url": "https://venturebeat.com/feed/",          "name": "VentureBeat",         "region": "world"},
]

TOPIC_KEYWORDS = {
    "investment": ["invest", "funding", "venture", "capital", "ipo", "series", "raise", "acquisition", "grant", "fdi"],
    "startup":    ["startup", "founder", "entrepreneur", "launch", "seed", "accelerator", "incubator", "pitch"],
    "insights":   ["strategy", "insight", "trend", "analysis", "economy", "market", "growth", "forecast", "reform"],
    "breakdown":  ["fintech", "banking", "infrastructure", "platform", "technology", "digital", "ai", "saas", "breakdown"],
}

REGION_INCLUDES = {
    "uz":    {"uz"},
    "ca":    {"uz", "ca"},
    "world": {"uz", "ca", "world"},
}

GEO_FILTER = {
    "uz": ["uzbekistan", "tashkent", "it park", "uzcombinator", "yoshlar", "o'zbekiston"],
    "ca": ["uzbekistan", "kazakhstan", "central asia", "tashkent", "almaty",
           "kyrgyzstan", "tajikistan", "turkmenistan", "astana"],
    "world": [],
}


async def _fetch_one(session: aiohttp.ClientSession, source: dict, topic: str, region: str) -> list[dict]:
    if source["region"] not in REGION_INCLUDES.get(region, {"world"}):
        return []
    try:
        async with session.get(source["url"], timeout=aiohttp.ClientTimeout(total=5)) as resp:
            text = await resp.text()
        feed      = feedparser.parse(text)
        geo_kws   = GEO_FILTER.get(region, [])
        topic_kws = TOPIC_KEYWORDS.get(topic, [])
        results   = []

        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            desc  = BeautifulSoup(entry.get("summary", "") or "", "html.parser").get_text()[:300]
            url   = entry.get("link", "")
            if not title or not url:
                continue
            combined = (title + " " + desc).lower()
            # Apply geo filter only for world-tagged sources on uz/ca queries
            if geo_kws and source["region"] == "world":
                if not any(k in combined for k in geo_kws):
                    continue
            if not any(k in combined for k in topic_kws):
                continue
            results.append({
                "title":       title,
                "description": desc.strip(),
                "url":         url,
                "source":      source["name"],
                "published":   entry.get("published", ""),
                "origin":      "rss",
                "date":        None,
            })
        return results
    except Exception:
        return []


async def fetch_rss(topic: str, region: str) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks   = [_fetch_one(session, src, topic, region) for src in RSS_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    articles = []
    for r in results:
        if isinstance(r, list):
            articles.extend(r)
    return articles
