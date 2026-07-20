"""
Shortlist filter rules - FR-1.3, FR-1.6.

Kept as pure functions with no I/O so they're trivial to unit test:
give them a list of dicts, get a shortlist back.
"""

from typing import Any

from scraper.config import config


def apply_filters(
    products: list[dict[str, Any]],
    require_rating: bool = True,
) -> list[dict[str, Any]]:
    """Applies rating/sold-count thresholds and returns the top shortlist,
    ranked by units sold - our stand-in for "trending" now that no
    commission or seller-side sales-velocity data is available on the
    public storefront.

    FR-1.6: callers must check for an empty result themselves and flag
    it - this function stays silent on purpose so it's reusable in tests.
    """
    passing = [p for p in products if _passes_thresholds(p, require_rating)]
    return sorted(passing, key=lambda p: p["units_sold"], reverse=True)[: config.shortlist_size]


def _passes_thresholds(product: dict[str, Any], require_rating: bool) -> bool:
    if require_rating and product.get("review_score", 0) < config.min_review_score:
        return False
    if product.get("units_sold", 0) < config.min_units_sold:
        return False
    return True
