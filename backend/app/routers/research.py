# backend/app/routers/research.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ResearchDossier
from app.services.pipeline import get_dossiers_for_product, review_research, start_research

router = APIRouter(prefix="/research", tags=["research"])


class ReviewRequest(BaseModel):
    approved: bool
    rejection_reason: str | None = None


@router.post("/{product_id}/generate", response_model=ResearchDossier)
def generate(product_id: int, session: Session = Depends(get_session)):
    try:
        return start_research(session, product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/product/{product_id}", response_model=list[ResearchDossier])
def list_for_product(product_id: int, session: Session = Depends(get_session)):
    """Feeds the card-detail view - newest dossier first, includes rejected ones."""
    return get_dossiers_for_product(session, product_id)


@router.post("/{dossier_id}/review", response_model=ResearchDossier)
def review(dossier_id: int, body: ReviewRequest, session: Session = Depends(get_session)):
    try:
        return review_research(session, dossier_id, body.approved, body.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))