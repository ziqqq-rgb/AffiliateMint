"""
Network response interception - the core of FR-1.2: read TikTok Shop's
internal API responses instead of the rendered page, so front-end
layout changes don't break the scraper as easily.

TODO: the field paths below (item["title"], etc.) are placeholders.
Open TikTok Shop, filter the browser Network tab to XHR/Fetch, search
for a product, and find the real response shape - then update
`parse_response` to match it.
"""

import json
from typing import Any

from playwright.async_api import Page, Response

from scraper.config import config


class ResponseCollector:
    """Collects matching network responses while a page is being driven."""

    def __init__(self) -> None:
        self.raw_payloads: list[dict[str, Any]] = []

    async def on_response(self, response: Response) -> None:
        if config.target_endpoint_pattern.strip("*") not in response.url:
            return
        try:
            body = await response.json()
        except Exception:
            return  # not JSON, or unrelated - ignore, don't crash the whole run
        self.raw_payloads.append(body)

    def attach(self, page: Page) -> None:
        page.on("response", self.on_response)


def parse_response(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn one raw API response into a list of parsed product dicts.

    FR-1.4: the raw payload is kept separately by the caller, so if
    this parsing logic is wrong or TikTok changes field names, no data
    is lost - only re-parsing is needed once the fix lands.
    """
    items = raw_payload.get("items", [])  # TODO: confirm the real top-level key
    parsed = []
    for item in items:
        parsed.append(
            {
                "title": item.get("title", ""),
                "price_rm": _to_float(item.get("price")),
                "commission_percentage": _to_float(item.get("commission_rate")),
                "review_score": _to_float(item.get("rating")),
                "stock_volume": int(item.get("stock", 0)),
                "units_sold": int(item.get("sold_count", 0)),
                "product_url": item.get("product_url", ""),
                "raw_payload": json.dumps(item),
            }
        )
    return parsed


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
