"""HTTP layer for the Kanban board itself (FR-4.1, FR-4.2, FR-4.3)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import CardStatus, ContentCard
from app.services.pipeline import advance_card_status

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=list[ContentCard])
def list_cards(session: Session = Depends(get_session)):
    """FR-4.1: everything the Kanban board needs to render its columns."""
    return session.exec(select(ContentCard)).all()


@router.post("/{card_id}/status", response_model=ContentCard)
def set_status(card_id: int, new_status: CardStatus, session: Session = Depends(get_session)):
    """FR-4.1: manual moves through Filming -> Ready to Post -> Posted."""
    try:
        return advance_card_status(session, card_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
