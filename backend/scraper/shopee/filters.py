"""Shortlist rules — pure functions, unit-testable like scraper/filters.py."""
from typing import Any

from scraper.shopee.config import config


def apply_filters(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    passing = [p for p in products if _passes_thresholds(p)]
    return sorted(passing, key=lambda p: p["commission_rate_pct"], reverse=True)[: config.shortlist_size]


def _passes_thresholds(product: dict[str, Any]) -> bool:
    if product.get("commission_rate_pct", 0) < config.min_commission_rate:
        return False
    if product.get("review_score", 0) < config.min_rating:
        return False
    return True