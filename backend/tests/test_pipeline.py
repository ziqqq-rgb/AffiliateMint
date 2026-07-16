"""
Smoke tests for the pipeline orchestration logic.

These use an in-memory SQLite DB and monkeypatch the Hermes call, so
they run without a live Hermes Agent or network access. The point is
to check the STATE MACHINE (status transitions), not the AI output.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import CardStatus, ResearchStatus, ScrapedProduct
from app.services import pipeline


@pytest.fixture()
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture()
def product(session) -> ScrapedProduct:
    p = ScrapedProduct(
        title="Mini fan",
        price_rm=25.0,
        commission_percentage=20.0,
        est_commission_rm=5.0,
        review_score=4.5,
        stock_volume=200,
        units_sold=1000,
        product_url="https://example.com",
        raw_payload="{}",
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _fake_dossier_data(_product):
    return {
        "what_it_does": "cools you down",
        "key_benefits": ["portable", "quiet", "rechargeable"],
        "usp": "smallest fan on the market",
        "review_summary_positive": "customers love the size",
        "review_summary_negative": "battery life could be better",
    }


def test_start_research_creates_pending_dossier(session, product, monkeypatch):
    monkeypatch.setattr(pipeline, "build_research_dossier", _fake_dossier_data)

    dossier = pipeline.start_research(session, product.id)

    assert dossier.status == ResearchStatus.PENDING
    assert dossier.product_id == product.id


def test_review_research_approve_advances_card(session, product, monkeypatch):
    monkeypatch.setattr(pipeline, "build_research_dossier", _fake_dossier_data)
    dossier = pipeline.start_research(session, product.id)

    reviewed = pipeline.review_research(session, dossier.id, approved=True)
    card = pipeline._card_for_product(session, product.id)

    assert reviewed.status == ResearchStatus.APPROVED
    assert card.status == CardStatus.RESEARCH_APPROVED


def test_review_research_reject_keeps_card_pending(session, product, monkeypatch):
    monkeypatch.setattr(pipeline, "build_research_dossier", _fake_dossier_data)
    dossier = pipeline.start_research(session, product.id)

    reviewed = pipeline.review_research(
        session, dossier.id, approved=False, rejection_reason="not a good fit"
    )
    card = pipeline._card_for_product(session, product.id)

    assert reviewed.status == ResearchStatus.REJECTED
    assert reviewed.rejection_reason == "not a good fit"
    assert card.status == CardStatus.RESEARCHED_PENDING  # unchanged - stays put on rejection
