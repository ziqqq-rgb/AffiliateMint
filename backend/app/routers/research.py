"""HTTP layer for the research stage - Approval Gate 1 (FR-2.3, FR-2.4)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ResearchDossier
from app.services.pipeline import review_research, start_research

router = APIRouter(prefix="/research", tags=["research"])


class ReviewRequest(BaseModel):
    approved: bool
    rejection_reason: str | None = None


@router.post("/{product_id}/run", response_model=ResearchDossier)
def run_research(product_id: int, session: Session = Depends(get_session)):
    try:
        return start_research(session, product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{dossier_id}/review", response_model=ResearchDossier)
def review(dossier_id: int, body: ReviewRequest, session: Session = Depends(get_session)):
    try:
        return review_research(session, dossier_id, body.approved, body.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
