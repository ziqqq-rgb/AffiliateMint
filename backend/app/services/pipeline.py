# backend/app/services/pipeline.py
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

from agents.memory import remember_edit
from agents.research_agent import build_research_dossier
from agents.script_agent import generate_scripts
from app.db import engine
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


def ensure_card_for_product(session: Session, product_id: int) -> ContentCard:
    card = _card_for_product(session, product_id)
    if card is None:
        card = ContentCard(product_id=product_id, status=CardStatus.SCRAPED)
        session.add(card)
        session.commit()
        session.refresh(card)
    return card


# --- Manual, gated stages -----------------------------------------------
# Kept for direct API/MCP use. The dashboard no longer calls these on their
# own - see the one-click flow below instead.

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

    card = ensure_card_for_product(session, product_id)
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


def start_scripting(session: Session, dossier_id: int) -> list[ScriptVariation]:
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None:
        raise ValueError(f"No ResearchDossier with id {dossier_id}")
    if dossier.status != ResearchStatus.APPROVED:
        raise ValueError("Dossier must be approved before scripting")

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


# --- Script editing (point 3) --------------------------------------------

def edit_script(session: Session, script_id: int, fields: dict) -> ScriptVariation:
    """Lets the operator hand-tune a generated script. The saved edit is also
    written into Hermes' memory ledger (agents/memory.py) so future scripts
    lean toward hooks/angles the operator actually kept - the other half of
    the FR-3.4 feedback loop, alongside earnings."""
    script = session.get(ScriptVariation, script_id)
    if script is None:
        raise ValueError(f"No ScriptVariation with id {script_id}")

    for field, value in fields.items():
        setattr(script, field, value)
    session.add(script)
    session.commit()
    session.refresh(script)

    remember_edit(script)
    return script


def select_script(session: Session, script_id: int) -> ContentCard:
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


# --- One-click pipeline (point 2) ----------------------------------------
# Research immediately followed by scripting, no approve/reject gate in
# between - the operator's only manual step is select_script above.

def start_full_pipeline(session: Session, product_id: int) -> ContentCard:
    """Flips the `is_generating` lock and returns immediately. Raises if a
    run is already in progress, so a double-click (or a re-mounted button
    after navigating back) can never kick off a second run - this is what
    was producing 6 scripts instead of 3."""
    card = ensure_card_for_product(session, product_id)
    if card.is_generating:
        raise ValueError("Pipeline is already running for this product")

    card.is_generating = True
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def run_full_pipeline_task(product_id: int) -> None:
    """Runs as a FastAPI BackgroundTask - opens its own DB session since the
    request's session closes as soon as the HTTP response goes out, which
    happens immediately (see start_full_pipeline)."""
    with Session(engine) as session:
        card = _card_for_product(session, product_id)
        if card is None:
            return

        try:
            product = session.get(ScrapedProduct, product_id)
            data = build_research_dossier(product)
            dossier = ResearchDossier(
                product_id=product_id,
                what_it_does=data["what_it_does"],
                key_benefits=json.dumps(data["key_benefits"]),
                usp=data["usp"],
                review_summary_positive=data["review_summary_positive"],
                review_summary_negative=data["review_summary_negative"],
                status=ResearchStatus.APPROVED,  # auto-approved - no manual gate in this flow
            )
            session.add(dossier)
            session.commit()
            session.refresh(dossier)

            for entry in generate_scripts(dossier):
                session.add(
                    ScriptVariation(
                        product_id=product_id,
                        angle_type=entry["angle_type"],
                        hook_ms=entry["hook_ms"],
                        body_ms=entry["body_ms"],
                        cta_ms=entry["cta_ms"],
                        caption_ms=entry["caption_ms"],
                        hashtags=json.dumps(entry["hashtags"]),
                        visual_notes=entry["visual_notes"],
                    )
                )

            card.status = CardStatus.SCRIPTED_PENDING
            card.used_auto_pipeline = True  # marks it for History (point 4)
        finally:
            card.is_generating = False  # always release the lock, success or failure
            session.add(card)
            session.commit()


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


def get_dossiers_for_product(session: Session, product_id: int) -> list[ResearchDossier]:
    statement = (
        select(ResearchDossier)
        .where(ResearchDossier.product_id == product_id)
        .order_by(ResearchDossier.created_at.desc())
    )
    return list(session.exec(statement))


def get_scripts_for_product(session: Session, product_id: int) -> list[ScriptVariation]:
    statement = select(ScriptVariation).where(ScriptVariation.product_id == product_id)
    return list(session.exec(statement))