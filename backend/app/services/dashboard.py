from sqlmodel import Session, select

from app.models import CardStatus, ContentCard, EarningsEntry
from app.services.feedback import cards_missing_earnings


def get_dashboard_summary(session: Session) -> dict:
    cards = session.exec(select(ContentCard)).all()
    earnings = session.exec(select(EarningsEntry)).all()

    cards_by_status = {status.value: 0 for status in CardStatus}
    for card in cards:
        cards_by_status[card.status.value] += 1

    return {
        "total_cards": len(cards),
        "cards_by_status": cards_by_status,
        "total_commission_rm": round(sum(e.commission_earned_rm for e in earnings), 2),
        "total_views": sum(e.views for e in earnings),
        "total_units_sold": sum(e.units_sold for e in earnings),
        "cards_missing_earnings": len(cards_missing_earnings(session)),
    }