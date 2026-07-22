"""Thin HTTP layer for scraped products. No business logic here -
see app/services/pipeline.py for what actually happens on each action."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import ContentCard, ScrapedProduct
from app.services.pipeline import run_full_pipeline_task, start_full_pipeline

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ScrapedProduct])
def list_products(session: Session = Depends(get_session)):
    return session.exec(select(ScrapedProduct)).all()


@router.get("/{product_id}", response_model=ScrapedProduct)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(ScrapedProduct, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"No product with id {product_id}")
    return product


@router.post("/{product_id}/run-pipeline", response_model=ContentCard)
def run_pipeline(product_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """One-click research + scripts (point 2). Returns immediately; poll
    GET /cards/{id} and watch `is_generating` to track progress."""
    try:
        card = start_full_pipeline(session, product_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    background_tasks.add_task(run_full_pipeline_task, product_id)
    return card