from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import CardStatus, ContentCard
from app.services.pipeline import add_card_to_progress, advance_card_status

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=list[ContentCard])
def list_cards(in_progress: bool | None = None, session: Session = Depends(get_session)):
    """Board calls this with in_progress=false, Progress calls it with
    in_progress=true. Omit the param to get everything."""
    statement = select(ContentCard)
    if in_progress is True:
        statement = statement.where(ContentCard.added_to_progress_at.is_not(None))
    elif in_progress is False:
        statement = statement.where(ContentCard.added_to_progress_at.is_(None))
    return session.exec(statement).all()


@router.get("/{card_id}", response_model=ContentCard)
def get_card(card_id: int, session: Session = Depends(get_session)):
    card = session.get(ContentCard, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"No card with id {card_id}")
    return card


@router.post("/{card_id}/add-to-progress", response_model=ContentCard)
def add_to_progress(card_id: int, session: Session = Depends(get_session)):
    """The Board's "Work on this" button calls this."""
    try:
        return add_card_to_progress(session, card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{card_id}/status", response_model=ContentCard)
def set_status(card_id: int, new_status: CardStatus, session: Session = Depends(get_session)):
    try:
        return advance_card_status(session, card_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))