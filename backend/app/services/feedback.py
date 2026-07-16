"""
Manual earnings feedback loop.

FR-4.4 - FR-4.6: the operator types in numbers by hand; this module
logs them and turns them into the memory entries the Script agent
searches before writing new scripts (see agents/memory.py). This is
also the only place that computes the "cards missing an earnings
entry" reminder list.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from agents.memory import remember_performance
from app.models import CardStatus, ContentCard, EarningsEntry, ScriptVariation


def log_earnings(
    session: Session,
    card_id: int,
    views: int = 0,
    likes: int = 0,
    units_sold: int = 0,
    commission_earned_rm: float = 0.0,
    notes: Optional[str] = None,
) -> EarningsEntry:
    """FR-4.4: record what the operator saw in the TikTok app for one card."""
    entry = EarningsEntry(
        card_id=card_id,
        views=views,
        likes=likes,
        units_sold=units_sold,
        commission_earned_rm=commission_earned_rm,
        notes=notes,
    )
    session.add(entry)

    card = session.get(ContentCard, card_id)
    if card:
        card.status = CardStatus.EARNINGS_LOGGED
        session.add(card)

    session.commit()
    session.refresh(entry)

    # Feed the result back into Hermes' memory so future scripts can
    # reference "what worked before" (FR-3.4, design doc section on
    # the manual earnings feedback loop).
    if card and card.selected_script_id:
        script = session.get(ScriptVariation, card.selected_script_id)
        if script:
            remember_performance(script=script, earnings=entry)

    return entry


def cards_missing_earnings(session: Session, days_since_posted: int = 3) -> list[ContentCard]:
    """FR-4.6: reminder list - posted cards with no earnings entry after N days."""
    cutoff = datetime.utcnow() - timedelta(days=days_since_posted)
    statement = select(ContentCard).where(
        ContentCard.status == CardStatus.POSTED,
        ContentCard.posted_at.is_not(None),
        ContentCard.posted_at < cutoff,
    )
    return list(session.exec(statement))
