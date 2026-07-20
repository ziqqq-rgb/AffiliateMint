"""
Scraper endpoint pattern and filter thresholds - isolated here on
purpose (NFR 5.5 Maintainability): this is the part most likely to
break when TikTok changes their site, so it should be the only file
you need to touch when that happens.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScraperConfig:
    # Captured from a real browser session's Network tab (DevTools -> XHR).
    # Currently only the homepage product feed - NOT scoped to a search
    # term or category yet. Capture a category/search page's endpoint the
    # same way and add a second pattern here when that's needed.
    target_endpoint_pattern: str = "*/api/shop/my/homepage_desktop/products_by_component*"
    search_url_template: str = "https://shop.tiktok.com/my"

    # No commission data exists on the public storefront (design doc
    # FR-1.3 note) - shortlisting instead favors well-reviewed,
    # fast-moving products.
    min_review_score: float = 4.0
    min_units_sold: int = 100
    shortlist_size: int = 5

    # NFR 5.2 scraping safety: keep these conservative, randomized
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 6.0


config = ScraperConfig()
