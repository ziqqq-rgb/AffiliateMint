"""Bridges scraper/shopee/run.py to the DB — same role as
app/services/scraping_pipeline.py, kept separate since the field
mapping (commission_rate, affiliate_link) differs from TikTok's."""
import asyncio
import json
import logging

from sqlmodel import Session, select

from app.models import Platform, ScrapedProduct
from app.services.pipeline import ensure_card_for_product
from scraper.shopee.run import run_shopee_scraper

logger = logging.getLogger(__name__)


def _item_to_product_kwargs(item: dict) -> dict:
    return {
        "tiktok_product_id": item["shopee_item_id"],
        "platform": Platform.SHOPEE,
        "title": item.get("title", ""),
        "price_rm": item.get("price_rm", 0.0),
        "original_price_rm": item.get("original_price_rm", 0.0),
        "review_score": item.get("review_score", 0.0),
        "review_count": item.get("review_count", 0),
        "units_sold": item.get("units_sold", 0),
        "shop_name": item.get("shop_name", ""),
        "image_url": item.get("image_url", ""),
        "product_url": item.get("product_url", ""),
        "commission_rate_pct": item.get("commission_rate_pct", 0.0),
        "affiliate_link": item.get("affiliate_link", ""),
        "raw_payload": json.dumps(item),
    }


def save_shopee_products(session: Session, items: list[dict]) -> list[ScrapedProduct]:
    saved = []
    for item in items:
        kwargs = _item_to_product_kwargs(item)
        product_id = kwargs["tiktok_product_id"]
        if not product_id:
            continue

        existing = session.exec(
            select(ScrapedProduct).where(
                ScrapedProduct.tiktok_product_id == product_id,
                ScrapedProduct.platform == Platform.SHOPEE,
            )
        ).first()

        if existing:
            for field, value in kwargs.items():
                setattr(existing, field, value)
            product = existing
        else:
            product = ScrapedProduct(**kwargs)

        session.add(product)
        saved.append(product)

    session.commit()
    for p in saved:
        session.refresh(p)
        ensure_card_for_product(session, p.id)
    return saved


class ShopeeScrapingService:
    @staticmethod
    def _execute_sync_scrape(min_commission_rate: float | None) -> dict:
        try:
            return {"success": True, "items": run_shopee_scraper(min_commission_rate)}
        except Exception as e:
            logger.error(f"Shopee scrape failed: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def run_async_pipeline(cls, min_commission_rate: float | None = None) -> dict:
        return await asyncio.to_thread(cls._execute_sync_scrape, min_commission_rate)