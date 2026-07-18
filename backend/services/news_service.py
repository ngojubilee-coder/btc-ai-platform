"""News service — fetch and correlate crypto/macro news events."""
import asyncio
import feedparser
import httpx
from datetime import datetime, timedelta, timezone
from core.config import settings
from core.logging_config import logger
from core.rag import rag_engine
from db.supabase_client import get_supabase


RSS_FEEDS = [
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "source": "CoinDesk", "type": "market"},
    {"url": "https://cointelegraph.com/rss", "source": "Cointelegraph", "type": "market"},
    {"url": "https://bitcoinmagazine.com/.rss/full/", "source": "Bitcoin Magazine", "type": "market"},
    {"url": "https://www.theblock.co/rss.xml", "source": "The Block", "type": "market"},
    {"url": "https://feeds.federalreserve.gov/feeds/press.xml", "source": "FED", "type": "fed"},
]

EVENT_KEYWORDS = {
    "fed": ["fed", "federal reserve", "fomc", "powell", "rate decision"],
    "cpi": ["cpi", "inflation", "consumer price"],
    "rate": ["interest rate", "rate cut", "rate hike", "basis points"],
    "etf": ["etf", "spot bitcoin", "blackrock", "fidelity", "ark invest"],
    "halving": ["halving", "block reward", "subsidy"],
    "liquidation": ["liquidation", "long squeeze", "short squeeze", "cascade"],
    "hack": ["hack", "exploit", "breach", "stolen", "drained"],
    "regulation": ["sec", "regulation", "lawsuit", "enforcement", "ban", "approval"],
    "whale": ["whale", "large transaction", "wallet", "transfer"],
    "mining": ["mining", "hashrate", "miner", "pool", "difficulty"],
}


def classify_event(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return event_type
    return "market"


async def fetch_rss_news(limit_per_feed: int = 20) -> list[dict]:
    """Fetch news from RSS feeds."""
    all_news = []
    for feed_info in RSS_FEEDS:
        try:
            feed = await asyncio.to_thread(feedparser.parse, feed_info["url"])
            for entry in feed.entries[:limit_per_feed]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                published = entry.get("published_parsed", entry.get("updated_parsed"))
                if published:
                    dt = datetime(*published[:6])
                else:
                    dt = datetime.now(timezone.utc)

                event_type = classify_event(title, summary)
                all_news.append({
                    "title": title,
                    "summary": summary[:500],
                    "content": summary,
                    "source": feed_info["source"],
                    "event_type": event_type,
                    "url": entry.get("link", ""),
                    "event_date": dt.isoformat(),
                })
        except Exception as e:
            logger.error(f"RSS error ({feed_info['source']}): {e}")
    return all_news


async def fetch_cryptocompare_news(limit: int = 50) -> list[dict]:
    """Fetch news from CryptoCompare API."""
    if not settings.cryptocompare_api_key:
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://min-api.cryptocompare.com/data/v2/news/",
                params={"lang": "EN", "limit": limit, "api_key": settings.cryptocompare_api_key},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("Data", [])
                news = []
                for item in data:
                    title = item.get("title", "")
                    body = item.get("body", "")[:500]
                    event_type = classify_event(title, body)
                    news.append({
                        "title": title,
                        "summary": body,
                        "content": body,
                        "source": item.get("source_info", {}).get("name", "CryptoCompare"),
                        "event_type": event_type,
                        "url": item.get("url", ""),
                        "event_date": datetime.fromtimestamp(item.get("published_on", 0)).isoformat(),
                    })
                return news
    except Exception as e:
        logger.error(f"CryptoCompare error: {e}")
    return []


async def fetch_newsapi_news(limit: int = 50) -> list[dict]:
    """Fetch news from NewsAPI.org."""
    if not settings.newsapi_key:
        return []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": "bitcoin OR BTC OR cryptocurrency",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "apiKey": settings.newsapi_key,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                news = []
                for item in articles:
                    title = item.get("title", "")
                    desc = item.get("description", "")[:500]
                    event_type = classify_event(title, desc)
                    news.append({
                        "title": title,
                        "summary": desc,
                        "content": item.get("content", desc),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "event_type": event_type,
                        "url": item.get("url", ""),
                        "event_date": item.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                    })
                return news
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
    return []


async def index_news_batch(news_list: list[dict]) -> int:
    """Index news events into the database with embeddings."""
    count = 0
    for news in news_list:
        try:
            await rag_engine.index_news(
                title=news["title"],
                summary=news["summary"],
                content=news["content"],
                source=news["source"],
                event_type=news["event_type"],
                event_date=news["event_date"],
                url=news["url"],
            )
            count += 1
        except Exception as e:
            logger.error(f"Index news error: {e}")
    return count


async def search_news_events(start_date: str | None = None, end_date: str | None = None, event_type: str | None = None, limit: int = 20, offset: int = 0) -> list[dict]:
    """Search news events from the database."""
    sb = get_supabase()
    q = sb.table("news_events").select("*")
    if start_date:
        q = q.gte("event_date", start_date)
    if end_date:
        q = q.lte("event_date", end_date)
    if event_type:
        q = q.eq("event_type", event_type)
    res = q.order("event_date", desc=True).range(offset, offset + limit - 1).execute()
    return res.data


async def correlate_price_movement(date: str, price_change_pct: float) -> dict:
    """Find news events that correlate with a significant price movement."""
    dt = datetime.fromisoformat(date)
    news = await search_news_events(
        start_date=(dt - timedelta(hours=24)).isoformat(),
        end_date=(dt + timedelta(hours=24)).isoformat(),
        limit=20,
    )
    return {
        "date": date,
        "price_change_pct": price_change_pct,
        "correlated_events": news,
        "n_events": len(news),
    }


async def refresh_news() -> dict:
    """Fetch and index all news from all sources."""
    rss_news = await fetch_rss_news()
    cc_news = await fetch_cryptocompare_news()
    newsapi_news = await fetch_newsapi_news()
    all_news = rss_news + cc_news + newsapi_news
    indexed = await index_news_batch(all_news)
    return {"fetched": len(all_news), "indexed": indexed}
