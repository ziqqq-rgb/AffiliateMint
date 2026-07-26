"""Shortlist rules — pure functions, unit-testable like scraper/filters.py."""
from typing import Any

from scraper.shopee.config import config


def apply_filters(
    products: list[dict[str, Any]],
    min_commission_rate: float | None = None,
    min_rating: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    known_item_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filters + ranks scraped offers. Any threshold left as None falls
    back to the config default (min_price/max_price have no default —
    they're simply skipped when not given).

    known_item_ids (optional): products already in the DB. When given,
    NEW products are ranked ahead of already-known ones - otherwise a
    fresh scrape can fill its entire shortlist with products you already
    have, silently discarding genuinely new finds that just had a
    slightly lower commission rate.
    """
    effective_commission = min_commission_rate if min_commission_rate is not None else config.min_commission_rate
    effective_rating = min_rating if min_rating is not None else config.min_rating
    known_item_ids = known_item_ids or set()

    passing = [
        p for p in products
        if _passes_thresholds(p, effective_commission, effective_rating, min_price, max_price)
    ]

    def sort_key(p: dict[str, Any]) -> tuple[bool, float]:
        is_new = p["shopee_item_id"] not in known_item_ids
        return (is_new, p["commission_rate_pct"])  # new=True sorts after False when reverse=True

    ranked = sorted(passing, key=sort_key, reverse=True)
    return ranked[: config.shortlist_size]


def _passes_thresholds(
    product: dict[str, Any],
    min_commission_rate: float,
    min_rating: float,
    min_price: float | None,
    max_price: float | None,
) -> bool:
    if product.get("commission_rate_pct", 0) < min_commission_rate:
        return False
    if product.get("review_score", 0) < min_rating:
        return False
    if min_price is not None and product.get("price_rm", 0) < min_price:
        return False
    if max_price is not None and product.get("price_rm", 0) > max_price:
        return False
    return True