"""Isolated config for the Shopee affiliate scraper — same role as
scraper/config.py has for TikTok."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShopeeScraperConfig:
    offer_list_endpoint_hint: str = "api/v3/offer/product/list" 
    get_link_endpoint_hint: str = "productOfferLinks"
    offer_page_url: str = "https://affiliate.shopee.com.my/offer/product_offer"

    min_commission_rate: float = 10.0
    min_rating: float = 4.0
    shortlist_size: int = 10
    max_pages: int = 5

    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 6.0


config = ShopeeScraperConfig()