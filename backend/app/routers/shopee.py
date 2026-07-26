from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ScrapedProduct
from app.services.shopee_pipeline import ShopeeScrapingService, save_shopee_products

router = APIRouter(prefix="/shopee", tags=["shopee"])


class ShopeeScrapeRequest(BaseModel):
    min_commission_rate: float | None = None
    min_rating: float | None = None
    min_price: float | None = None
    max_price: float | None = None


@router.post("/scrape", response_model=list[ScrapedProduct])
async def trigger_scrape(payload: ShopeeScrapeRequest, session: Session = Depends(get_session)):
    result = await ShopeeScrapingService.run_async_pipeline(
        session, payload.min_commission_rate, payload.min_rating, payload.min_price, payload.max_price
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
 
    return save_shopee_products(session, result["items"])