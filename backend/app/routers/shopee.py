from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ScrapedProduct
from app.services.shopee_pipeline import ShopeeScrapingService, save_shopee_products

router = APIRouter(prefix="/shopee", tags=["shopee"])


class ShopeeScrapeRequest(BaseModel):
    min_commission_rate: float | None = None


@router.post("/scrape", response_model=list[ScrapedProduct])
async def trigger_scrape(payload: ShopeeScrapeRequest, session: Session = Depends(get_session)):
    result = await ShopeeScrapingService.run_async_pipeline(payload.min_commission_rate)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return save_shopee_products(session, result["items"])