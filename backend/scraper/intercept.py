"""
Network response interception - the core of FR-1.2: read TikTok Shop's
internal API responses instead of the rendered page, so front-end
layout changes don't break the scraper as easily.

We never build or sign the request ourselves - TikTok's own page JS
does that (see the X-Tts-Oec-Bsid token on a real capture, which is a
generated anti-bot signature, not something to reverse-engineer). We
just let Playwright load the real page and listen for the response.
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
    """Turns one raw homepage-feed API response into parsed product dicts.

    FR-1.4: the raw payload is kept separately by the caller, so if
    this parsing logic is wrong or TikTok changes field names, no data
    is lost - only re-parsing is needed once the fix lands.
    """
    items = raw_payload.get("data", {}).get("productList", [])
    parsed = []
    for item in items:
        price_info = item.get("product_price_info", {})
        rate_info = item.get("rate_info", {})
        sold_info = item.get("sold_info", {})
        seller_info = item.get("seller_info", {})
        seo_url = item.get("seo_url", {})
        images = item.get("image", {}).get("url_list", [])

        parsed.append(
            {
                "tiktok_product_id": item.get("product_id", ""),
                "title": item.get("title", ""),
                "price_rm": _to_float(price_info.get("sale_price_decimal")),
                "original_price_rm": _to_float(price_info.get("origin_price_decimal")),
                "review_score": _to_float(rate_info.get("score")),
                "review_count": _to_int(rate_info.get("review_count")),
                "units_sold": _to_int(sold_info.get("sold_count")),
                "shop_name": seller_info.get("shop_name", ""),
                "image_url": images[0] if images else "",
                "product_url": seo_url.get("canonical_url", ""),
                "raw_payload": json.dumps(item),
            }
        )
    return parsed


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
