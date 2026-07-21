"""
Bridges FastAPI/MCP callers to the synchronous SeleniumBase + Playwright
scraper in scraper/run.py, and persists its output as ScrapedProduct rows
(design doc 3.3: "Scraper Service -> writes ScrapedProduct rows to DB").
"""
import asyncio
import json
import logging
from typing import Any, Dict

from sqlmodel import Session, select

from app.models import ScrapedProduct
from scraper.run import run_hybrid_scraper

logger = logging.getLogger(__name__)


def _item_to_product_kwargs(item: dict) -> dict:
    """Maps one harvested item (scraper/run.py's field names) onto
    ScrapedProduct's schema (app/models.py). Kept as its own function so a
    field-name change on either side only needs one edit here."""
    return {
        "tiktok_product_id": str(item.get("product_id", "")),
        "title": item.get("title", ""),
        "price_rm": float(item.get("sale_price_rm") or 0.0),
        "original_price_rm": float(item.get("original_price_rm") or 0.0),
        "review_score": float(item.get("rating_score") or 0.0),
        "review_count": int(item.get("review_count") or 0),
        "units_sold": int(item.get("units_sold") or 0),
        "shop_name": item.get("shop_name", ""),
        "image_url": item.get("image_url", ""),
        "product_url": item.get("product_url", ""),
        "raw_payload": json.dumps(item),  # FR-1.4: keep raw data even if parsing above is wrong
    }


def save_scraped_products(session: Session, items: list[dict]) -> list[ScrapedProduct]:
    """Upserts by tiktok_product_id so re-running a scrape doesn't duplicate
    rows - it refreshes price/rating/sold count on the existing row instead."""
    saved = []
    for item in items:
        kwargs = _item_to_product_kwargs(item)
        product_id = kwargs["tiktok_product_id"]
        if not product_id:
            continue

        existing = session.exec(
            select(ScrapedProduct).where(ScrapedProduct.tiktok_product_id == product_id)
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
    return saved


class ScrapingPipelineService:
    @staticmethod
    def _execute_sync_scrape(target_url: str) -> Dict[str, Any]:
        try:
            items = run_hybrid_scraper(target_url)
            return {"success": True, "items": items}
        except Exception as e:
            logger.error(f"Scrape failed for {target_url}: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def run_async_pipeline(cls, target_url: str) -> Dict[str, Any]:
        return await asyncio.to_thread(cls._execute_sync_scrape, target_url)