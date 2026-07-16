"""
Shortlist filter rules - FR-1.3, FR-1.6.

Kept as pure functions with no I/O so they're trivial to unit test:
give them a list of dicts, get a shortlist back.
"""

from typing import Any

from scraper.config import config


def apply_filters(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply commission/stock/rating thresholds and return the top shortlist.

    FR-1.6: callers must check for an empty result themselves and flag
    it - this function stays silent on purpose so it's reusable in tests.
    """
    passing = [p for p in products if _passes_thresholds(p)]
    ranked = sorted(passing, key=lambda p: p["est_commission_rm"], reverse=True)
    return ranked[: config.shortlist_size]


def _passes_thresholds(product: dict[str, Any]) -> bool:
    return (
        product.get("commission_percentage", 0) >= config.min_commission_pct
        and product.get("stock_volume", 0) >= config.min_stock
        and product.get("review_score", 0) >= config.min_review_score
    )
