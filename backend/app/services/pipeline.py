"""
Core state machine for the product -> dossier -> script -> card pipeline
(design doc 3.3 "Data Flow"). Each function is one status transition;
ContentCard.status is the single source of truth for the Kanban board (FR-4.1).

Scraping lives in app/services/scraping_pipeline.py - this file starts
downstream of that, at "a ScrapedProduct row already exists".
"""

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from agents.research_agent import build_research_dossier
from agents.script_agent import generate_scripts
from app.models import (
    CardStatus,
    ContentCard,
    ResearchDossier,
    ResearchStatus,
    ScrapedProduct,
    ScriptVariation,
)


def _card_for_product(session: Session, product_id: int) -> Optional[ContentCard]:
    statement = select(ContentCard).where(ContentCard.product_id == product_id)
    return session.exec(statement).first()


def _get_or_create_card(session: Session, product_id: int) -> ContentCard:
    card = _card_for_product(session, product_id)
    if card is None:
        card = ContentCard(product_id=product_id, status=CardStatus.SCRAPED)
        session.add(card)
        session.commit()
        session.refresh(card)
    return card


# --- Stage 1: Research (FR-2.1 - FR-2.4) ------------------------------------

def start_research(session: Session, product_id: int) -> ResearchDossier:
    product = session.get(ScrapedProduct, product_id)
    if product is None:
        raise ValueError(f"No ScrapedProduct with id {product_id}")

    data = build_research_dossier(product)
    dossier = ResearchDossier(
        product_id=product_id,
        what_it_does=data["what_it_does"],
        key_benefits=json.dumps(data["key_benefits"]),
        usp=data["usp"],
        review_summary_positive=data["review_summary_positive"],
        review_summary_negative=data["review_summary_negative"],
        status=ResearchStatus.PENDING,
    )
    session.add(dossier)

    card = _get_or_create_card(session, product_id)
    card.status = CardStatus.RESEARCHED_PENDING
    session.add(card)

    session.commit()
    session.refresh(dossier)
    return dossier


def review_research(
    session: Session,
    dossier_id: int,
    approved: bool,
    rejection_reason: Optional[str] = None,
) -> ResearchDossier:
    """Gate 1. Approving advances the card; rejecting archives the dossier
    in place (FR-2.4) and leaves the card where it is."""
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None:
        raise ValueError(f"No ResearchDossier with id {dossier_id}")

    if approved:
        dossier.status = ResearchStatus.APPROVED
        card = _card_for_product(session, dossier.product_id)
        if card:
            card.status = CardStatus.RESEARCH_APPROVED
            session.add(card)
    else:
        dossier.status = ResearchStatus.REJECTED
        dossier.rejection_reason = rejection_reason

    session.add(dossier)
    session.commit()
    session.refresh(dossier)
    return dossier


# --- Stage 2: Scripting (FR-3.1 - FR-3.6) -----------------------------------

def start_scripting(session: Session, dossier_id: int) -> list[ScriptVariation]:
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None:
        raise ValueError(f"No ResearchDossier with id {dossier_id}")
    if dossier.status != ResearchStatus.APPROVED:
        raise ValueError("Dossier must be approved before scripting (Gate 1)")

    variations = []
    for entry in generate_scripts(dossier):
        variation = ScriptVariation(
            product_id=dossier.product_id,
            angle_type=entry["angle_type"],
            hook_ms=entry["hook_ms"],
            body_ms=entry["body_ms"],
            cta_ms=entry["cta_ms"],
            caption_ms=entry["caption_ms"],
            hashtags=json.dumps(entry["hashtags"]),
            visual_notes=entry["visual_notes"],
        )
        session.add(variation)
        variations.append(variation)

    card = _card_for_product(session, dossier.product_id)
    if card:
        card.status = CardStatus.SCRIPTED_PENDING
        session.add(card)

    session.commit()
    for v in variations:
        session.refresh(v)
    return variations


def select_script(session: Session, script_id: int) -> ContentCard:
    """Gate 2 (FR-3.5/3.6). Selecting a variation makes it the card's
    single source of truth and moves the card to 'Ready to Film'."""
    script = session.get(ScriptVariation, script_id)
    if script is None:
        raise ValueError(f"No ScriptVariation with id {script_id}")

    script.is_selected = True
    session.add(script)

    card = _card_for_product(session, script.product_id)
    if card is None:
        raise ValueError(f"No ContentCard for product {script.product_id}")
    card.selected_script_id = script.id
    card.status = CardStatus.SCRIPT_APPROVED
    session.add(card)

    session.commit()
    session.refresh(card)
    return card


# --- Stage 3: Manual Kanban moves (FR-4.1) ----------------------------------

def advance_card_status(session: Session, card_id: int, new_status: CardStatus) -> ContentCard:
    card = session.get(ContentCard, card_id)
    if card is None:
        raise ValueError(f"No ContentCard with id {card_id}")

    card.status = new_status
    if new_status == CardStatus.FILMING and card.filmed_at is None:
        card.filmed_at = datetime.utcnow()
    if new_status == CardStatus.POSTED and card.posted_at is None:
        card.posted_at = datetime.utcnow()

    session.add(card)
    session.commit()
    session.refresh(card)
    return card