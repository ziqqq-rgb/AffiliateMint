# backend/app/routers/research.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import ResearchDossier
from app.services.pipeline import get_dossiers_for_product, start_research

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/{product_id}/generate", response_model=ResearchDossier)
def generate(product_id: int, session: Session = Depends(get_session)):
    try:
        return start_research(session, product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/product/{product_id}", response_model=list[ResearchDossier])
def list_for_product(product_id: int, session: Session = Depends(get_session)):
    """Feeds the card-detail view - newest dossier first."""
    return get_dossiers_for_product(session, product_id)