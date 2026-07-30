"""
backend/scraper/intercept.py

Pure JSON parsing for TikTok's homepage/product-feed API response - no
I/O, no browser. Kept deliberately small so it stays trivial to unit
test (see tests/test_scraper.py): feed it a dict, get ScrapedProduct-
shaped dicts back.

The live CDP wiretap that captures this JSON off the wire in the first
place lives in scraper/network_interceptor.py instead, since a
stateful class attached to a running browser has nothing to do with
this file's job of "reshape one already-captured payload."
"""


def parse_response(raw_response: dict) -> list[dict]:
    """Maps one homepage/product-feed API response into ScrapedProduct-
    shaped dicts (FR-1.1)."""
    items = raw_response.get("data", {}).get("productList", [])
    return [_parse_item(item) for item in items]


def _parse_item(item: dict) -> dict:
    price_info = item.get("product_price_info", {})
    rate_info = item.get("rate_info", {})
    sold_info = item.get("sold_info", {})
    seller_info = item.get("seller_info", {})
    seo_url = item.get("seo_url", {})
    image_urls = item.get("image", {}).get("url_list", [])

    return {
        "tiktok_product_id": str(item.get("product_id", "")),
        "title": item.get("title", ""),
        "price_rm": float(price_info.get("sale_price_decimal", 0.0) or 0.0),
        "original_price_rm": float(price_info.get("origin_price_decimal", 0.0) or 0.0),
        "review_score": float(rate_info.get("score", 0.0) or 0.0),
        "review_count": int(rate_info.get("review_count", 0) or 0),
        "units_sold": int(sold_info.get("sold_count", 0) or 0),
        "shop_name": seller_info.get("shop_name", ""),
        "image_url": image_urls[0] if image_urls else "",
        "product_url": seo_url.get("canonical_url", ""),
    }
