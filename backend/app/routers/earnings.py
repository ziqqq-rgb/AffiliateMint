"""HTTP layer for the manual earnings log (FR-4.4, FR-4.5, FR-4.6)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import EarningsEntry
from app.services.feedback import cards_missing_earnings, log_earnings

router = APIRouter(prefix="/earnings", tags=["earnings"])


class EarningsRequest(BaseModel):
    views: int = 0
    likes: int = 0
    units_sold: int = 0
    commission_earned_rm: float = 0.0
    notes: str | None = None


@router.post("/{card_id}", response_model=EarningsEntry)
def log(card_id: int, body: EarningsRequest, session: Session = Depends(get_session)):
    return log_earnings(
        session,
        card_id,
        views=body.views,
        likes=body.likes,
        units_sold=body.units_sold,
        commission_earned_rm=body.commission_earned_rm,
        notes=body.notes,
    )


@router.get("/reminders")
def reminders(session: Session = Depends(get_session)):
    """FR-4.6: cards posted 3+ days ago with no earnings entry yet."""
    cards = cards_missing_earnings(session)
    return {"card_ids": [c.id for c in cards]}
