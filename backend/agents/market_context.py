"""
Turns Firecrawl search results into a short context block for
research_agent's prompt.

Kept separate from firecrawl_client.py (raw HTTP) and research_agent.py
(prompt template) on purpose - this file's only job is noise reduction:
raw search results are full page scrapes (nav bars, carts, footers
included, as seen in real output - e.g. shopee.com.my's "Login
Required" wall), not clean article text.

clean_markdown() is public (not _prefixed) since deep_research_agent.py
reuses it for the same noise-reduction job on ingredient-topic search
results - one cleaning function, two callers.

REQUEST_LIMIT > MAX_RESULTS on purpose: self-hosted Firecrawl (no
Fire-Engine) drops a portion of result pages silently - a real test
requesting 5 came back with 3. Requesting extra and capping after
cleaning absorbs that attrition instead of starving the prompt.
"""
import re

from agents.providers.firecrawl_client import search
from app.models import ScrapedProduct

REQUEST_LIMIT = 8
MAX_RESULTS = 4
MAX_CHARS_PER_RESULT = 600


def clean_markdown(text: str) -> str:
    """Strips markdown images/links and collapses blank lines. Cheap
    noise reduction, not a full content extractor - callers should
    tell their prompt this may still contain leftover site clutter."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links -> plain text
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text


def build_market_context(product: ScrapedProduct) -> str:
    """Searches the open web for this product's category and returns a
    plain-text block, or "" if nothing useful came back - the prompt
    template treats "" as "no external context available", not an error.
    """
    query = f"{product.title} price Malaysia"
    results = search(query, limit=REQUEST_LIMIT)

    blocks = []
    for r in results:
        cleaned = clean_markdown(r.get("markdown", ""))[:MAX_CHARS_PER_RESULT]
        if cleaned:
            blocks.append(f"Source: {r.get('title', 'Unknown')} ({r.get('url', '')})\n{cleaned}")
        if len(blocks) >= MAX_RESULTS:
            break

    return "\n\n".join(blocks)