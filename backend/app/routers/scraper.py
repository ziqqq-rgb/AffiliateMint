"""HTTP layer for on-demand scraping (FR-1.5)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ScrapedProduct
from app.services.scraping_pipeline import ScrapingPipelineService, save_scraped_products

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    url: str = "https://shop.tiktok.com/my"


@router.post("/scrape", response_model=list[ScrapedProduct])
async def trigger_scrape(payload: ScrapeRequest, session: Session = Depends(get_session)):
    result = await ScrapingPipelineService.run_async_pipeline(payload.url)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return save_scraped_products(session, result["items"])