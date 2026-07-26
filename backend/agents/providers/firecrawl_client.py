"""
Firecrawl web-search client - grounds research_agent's prompt with real
market context (competitor pricing, category norms) pulled from the open
web. Deliberately NOT used to scrape TikTok or Shopee product pages
directly: manual testing confirmed Firecrawl blocks TikTok outright and
returns a login-walled empty shell for Shopee (see
scraper/manual_test_firecrawl_shopee.py's output). This client's only
job is the /search endpoint against the general web.
"""
import httpx

from agents.providers.common import call_with_retry
from app.config import settings

TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
SEARCH_URL = "https://api.firecrawl.dev/v1/search"


def search(query: str, limit: int = 5) -> list[dict]:
    """Returns up to `limit` results as {title, url, markdown} dicts.

    Returns [] on any failure (bad key, rate limit, network) instead of
    raising - missing market context should degrade the dossier's
    quality, not break generation entirely (see market_context.py).
    """
    def _call() -> list[dict]:
        response = httpx.post(
            SEARCH_URL,
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"query": query, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
        return body.get("data", []) if body.get("success") else []

    try:
        return call_with_retry(_call)
    except Exception as e:
        print(f"[WARN] Firecrawl search failed for query '{query}': {e}")
        return []