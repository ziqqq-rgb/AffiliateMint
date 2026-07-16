"""Thin HTTP layer for scraped products. No business logic here -
see app/services/pipeline.py for what actually happens on each action."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import ScrapedProduct

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ScrapedProduct])
def list_products(session: Session = Depends(get_session)):
    return session.exec(select(ScrapedProduct)).all()


@router.get("/{product_id}", response_model=ScrapedProduct)
def get_product(product_id: int, session: Session = Depends(get_session)):
    return session.get(ScrapedProduct, product_id)
