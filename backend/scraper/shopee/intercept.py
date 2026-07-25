"""Pure JSON parsing for Shopee's product_offer response — no I/O,
mirrors scraper/intercept.py::parse_response's role for TikTok."""
from typing import Any


def _pct_to_float(pct: str) -> float:
    """'6%' -> 6.0."""
    return float(pct.strip().rstrip("%") or 0.0) if pct else 0.0


def parse_offer_response(raw_response: dict) -> list[dict[str, Any]]:
    items = raw_response.get("data", {}).get("list", [])
    return [_parse_offer_item(item) for item in items]


def _parse_offer_item(item: dict) -> dict:
    card = item.get("batch_item_for_item_card_full", {})
    rating = card.get("item_rating", {})

    return {
        "shopee_item_id": item.get("item_id", ""),
        "shopee_shop_id": item.get("shop_id", ""),
        "title": card.get("name", ""),
        "price_rm": float(card.get("price", 0) or 0) / 100_000,           # Shopee prices are micro-units
        "original_price_rm": float(card.get("price_before_discount", 0) or 0) / 100_000,
        "review_score": round(float(rating.get("rating_star", 0.0) or 0.0), 2),
        "review_count": sum(rating.get("rating_count", []) or []),
        "units_sold": int(card.get("sold", 0) or 0),
        "shop_name": card.get("shop_name", ""),
        "image_url": f"https://cf.shopee.com.my/file/{card['image']}" if card.get("image") else "",
        "product_url": item.get("product_link", ""),
        # default_commission_rate matches the UI's total "Est. Commission"
        # (CommissionsXTRA + Shopee's own cut) — confirmed against your
        # screenshot's Offer Details panel.
        "commission_rate_pct": _pct_to_float(item.get("default_commission_rate", "0%")),
    }