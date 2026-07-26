"""
Firecrawl client - powers two things:
1. market_context.py's category grounding (used for every product)
2. deep_research_agent.py's ingredient/science search (skincare,
   supplements, etc - only when applicable)

Deliberately NOT used to scrape TikTok or Shopee product pages
directly: manual testing confirmed Firecrawl blocks TikTok outright and
returns a login-walled empty shell for Shopee (see
scraper/manual_test_firecrawl_shopee.py's output). This client's only
job is the /search endpoint against the general web.

firecrawl_api_base is configurable (app/config.py) so this same client
works against either the hosted API (default) or a self-hosted instance
(see infra/firecrawl/) without any code change - just an env var.
"""
import logging

import httpx

from agents.providers.common import call_with_retry
from app.config import settings

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


def search(query: str, limit: int = 5) -> list[dict]:
    """Returns up to `limit` results as {title, url, markdown} dicts.

    Returns [] on any failure (bad key, rate limit, network) instead of
    raising - missing market/research context should degrade dossier
    quality, not break generation entirely. Every [] path is logged so
    "genuinely no results" and "the request failed" aren't
    indistinguishable when debugging later.
    """
    def _call() -> list[dict]:
        headers = {}
        if settings.firecrawl_api_key:  # self-hosted default has no auth at all
            headers["Authorization"] = f"Bearer {settings.firecrawl_api_key}"

        response = httpx.post(
            f"{settings.firecrawl_api_base}/search",
            headers=headers,
            json={"query": query, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()

        if not body.get("success"):
            logger.warning(f"[firecrawl] search '{query}' returned success=false: {body}")
            return []

        return body.get("data", [])

    try:
        results = call_with_retry(_call)
    except Exception as e:
        logger.warning(f"[firecrawl] search failed for query '{query}': {e}")
        return []

    if not results:
        logger.info(f"[firecrawl] search '{query}' returned 0 results")

    return results