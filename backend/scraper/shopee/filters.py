"""Shortlist rules — pure functions, unit-testable like scraper/filters.py."""
from typing import Any

from scraper.shopee.config import config


def apply_filters(
    products: list[dict[str, Any]],
    min_commission_rate: float | None = None,
    min_rating: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict[str, Any]]:
    """Filters + ranks scraped offers. Any threshold left as None falls
    back to the config default (min_price/max_price have no default —
    they're simply skipped when not given)."""
    effective_commission = min_commission_rate if min_commission_rate is not None else config.min_commission_rate
    effective_rating = min_rating if min_rating is not None else config.min_rating

    passing = [
        p for p in products
        if _passes_thresholds(p, effective_commission, effective_rating, min_price, max_price)
    ]
    return sorted(passing, key=lambda p: p["commission_rate_pct"], reverse=True)[: config.shortlist_size]


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