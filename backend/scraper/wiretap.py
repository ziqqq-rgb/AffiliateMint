"""
backend/scraper/wiretap.py

Recursive JSON product extraction for scraper/run.py's network wiretap.
TikTok's API responses nest product objects at unpredictable depths, so
rather than parsing one known shape (like scraper/intercept.py does for
the homepage feed endpoint), this walks a whole response tree looking
for anything that looks like a product.
"""
from typing import Any, Callable

PRICE_KEYS = ("product_price_info", "price", "sale_price", "price_info", "sale_price_decimal")
TITLE_KEYS = ("title", "product_name", "name")
MIN_TITLE_LENGTH_FOR_MATCH = 5


def extract_rich_product_data(obj: dict) -> dict:
    """Maps one product-shaped dict (from anywhere in a JSON response)
    into the rich harvested-item shape scraper/run.py collects."""
    price_info = obj.get("product_price_info", {})
    rate_info = obj.get("rate_info", {})
    sold_info = obj.get("sold_info", {})
    seller_info = obj.get("seller_info", {})
    seo_url = obj.get("seo_url", {})
    image_urls = obj.get("image", {}).get("url_list", [])

    return {
        "product_id": str(obj.get("product_id", "")),
        "title": str(obj.get("title") or obj.get("product_name") or "").strip(),
        "sale_price_rm": str(price_info.get("sale_price_decimal") or price_info.get("sale_price") or "0.00"),
        "original_price_rm": str(price_info.get("origin_price_decimal") or price_info.get("origin_price") or "0.00"),
        "discount_percentage": str(price_info.get("discount_format", "")),
        "savings_amount": str(price_info.get("reduce_price_format", "")),
        "units_sold": int(sold_info.get("sold_count", 0)) if sold_info.get("sold_count") else 0,
        "rating_score": float(rate_info.get("score", 0.0)) if rate_info.get("score") else 0.0,
        "review_count": int(rate_info.get("review_count", 0))
        if str(rate_info.get("review_count", "0")).isdigit()
        else 0,
        "shop_name": str(seller_info.get("shop_name", "")),
        "shop_id": str(seller_info.get("seller_id", "")),
        "free_shipping": _has_free_shipping_label(obj),
        "product_url": str(seo_url.get("canonical_url", "")),
        "image_url": image_urls[0] if image_urls else "",
    }


def _has_free_shipping_label(obj: dict) -> bool:
    labels = obj.get("product_marketing_info", {}).get("placement_labels", {})
    for group in labels.values():
        if not isinstance(group, list):
            continue
        for label in group:
            text = str(label.get("text", "")).lower()
            if "free shipping" in text or label.get("da_info", "").find("free_shipping") != -1:
                return True
    return False


def _looks_like_product(obj: dict) -> bool:
    has_price = any(key in obj for key in PRICE_KEYS)
    has_title = any(key in obj for key in TITLE_KEYS) and len(str(obj.get("title", ""))) > MIN_TITLE_LENGTH_FOR_MATCH
    return has_price and has_title


def find_products(obj: Any, on_product: Callable[[dict], None]) -> None:
    """Walks a JSON response tree (dict/list, arbitrary depth) and calls
    on_product(extracted_dict) for every node that looks like a product.
    Takes a callback instead of returning a list so the caller can
    dedupe/log as matches stream in, same as before this was extracted.
    """
    if isinstance(obj, dict):
        if _looks_like_product(obj):
            rich_data = extract_rich_product_data(obj)
            if rich_data["title"] and float(rich_data["sale_price_rm"]) > 0:
                on_product(rich_data)
        else:
            for value in obj.values():
                find_products(value, on_product)
    elif isinstance(obj, list):
        for item in obj:
            find_products(item, on_product)
