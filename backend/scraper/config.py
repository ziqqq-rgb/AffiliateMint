"""
Scraper selectors, endpoints, and filter thresholds - isolated here on
purpose (NFR 5.5 Maintainability): this is the part most likely to
break when TikTok changes their site, so it should be the only file
you need to touch when that happens.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScraperConfig:
    # TODO: replace with the real TikTok Shop Malaysia network endpoint
    # you capture in the Playwright/browser network tab. This is a
    # placeholder - see scraper/intercept.py for how it's used.
    target_endpoint_pattern: str = "*/api/shop/product/search*"

    search_url_template: str = "https://shop.tiktok.com/search?q={query}"

    min_commission_pct: float = 15.0
    min_stock: int = 50
    min_review_score: float = 4.0
    shortlist_size: int = 5

    # NFR 5.2 scraping safety: keep these conservative, randomized
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 6.0


config = ScraperConfig()
