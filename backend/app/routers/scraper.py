from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ScrapedProduct
from app.services.scraping_pipeline import ScrapingPipelineService, save_scraped_products
from app.services.pipeline import clear_untouched_products


router = APIRouter(prefix="/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    url: str = "https://shop.tiktok.com/my"
    category: str | None = None
    min_rating: float | None = None
    sort_by_sold: bool = False
    min_price: float | None = None
    max_price: float | None = None


@router.post("/scrape", response_model=list[ScrapedProduct])
async def trigger_scrape(payload: ScrapeRequest, session: Session = Depends(get_session)):
    result = await ScrapingPipelineService.run_async_pipeline(
        payload.url,
        category=payload.category,
        min_rating=payload.min_rating,
        sort_by_sold=payload.sort_by_sold,
        min_price=payload.min_price,
        max_price=payload.max_price,
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return save_scraped_products(session, result["items"])


@router.delete("/clear")
def clear_scraped(session: Session = Depends(get_session)):
    deleted = clear_untouched_products(session)
    return {"deleted": deleted}