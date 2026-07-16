"""
Pipeline orchestration: moves a product through
scrape -> research -> approve -> script -> approve -> manual stages.

This is the only place that knows the ORDER of the pipeline. Routers
call these functions; they never talk to agents or the scraper
directly. That's what design doc section 3.3 calls the "assembly
line" - each station only touches the station next to it, through a
fixed shape (here: a DB row instead of JSON over the wire, but the
principle is identical).
"""

import json
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


def start_research(session: Session, product_id: int) -> ResearchDossier:
    """FR-2.1 - FR-2.3: run deep research on one scraped product."""
    product = session.get(ScrapedProduct, product_id)
    if product is None:
        raise ValueError(f"No scraped product with id {product_id}")

    dossier_data = build_research_dossier(product)
    dossier = ResearchDossier(
        product_id=product_id,
        what_it_does=dossier_data["what_it_does"],
        key_benefits=json.dumps(dossier_data["key_benefits"]),
        usp=dossier_data["usp"],
        review_summary_positive=dossier_data["review_summary_positive"],
        review_summary_negative=dossier_data["review_summary_negative"],
        status=ResearchStatus.PENDING,
    )
    session.add(dossier)

    card = ContentCard(product_id=product_id, status=CardStatus.RESEARCHED_PENDING)
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
    """FR-2.3 - FR-2.4: Approval Gate 1. Nothing scripts without this."""
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None:
        raise ValueError(f"No research dossier with id {dossier_id}")

    dossier.status = ResearchStatus.APPROVED if approved else ResearchStatus.REJECTED
    dossier.rejection_reason = None if approved else rejection_reason
    session.add(dossier)

    card = _card_for_product(session, dossier.product_id)
    if card and approved:
        card.status = CardStatus.RESEARCH_APPROVED
        session.add(card)

    session.commit()
    session.refresh(dossier)
    return dossier


def start_scripting(session: Session, dossier_id: int) -> list[ScriptVariation]:
    """FR-3.1 - FR-3.4: write 3 script angles for an approved dossier."""
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None or dossier.status != ResearchStatus.APPROVED:
        raise ValueError("Dossier must be approved before scripting can start")

    variations_data = generate_scripts(dossier)
    variations = []
    for v in variations_data:
        variation = ScriptVariation(
            product_id=dossier.product_id,
            angle_type=v["angle_type"],
            hook_ms=v["hook_ms"],
            body_ms=v["body_ms"],
            cta_ms=v["cta_ms"],
            caption_ms=v["caption_ms"],
            hashtags=json.dumps(v["hashtags"]),
            visual_notes=v["visual_notes"],
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
    """FR-3.5 - FR-3.6: operator picks the final script. Card becomes Ready to Film."""
    script = session.get(ScriptVariation, script_id)
    if script is None:
        raise ValueError(f"No script variation with id {script_id}")

    script.is_selected = True
    session.add(script)

    card = _card_for_product(session, script.product_id)
    if card is None:
        raise ValueError(f"No content card for product {script.product_id}")
    card.selected_script_id = script.id
    card.status = CardStatus.SCRIPT_APPROVED
    session.add(card)

    session.commit()
    session.refresh(card)
    return card


def advance_card_status(session: Session, card_id: int, new_status: CardStatus) -> ContentCard:
    """FR-4.1: manual status moves (Filming -> Ready to Post -> Posted).
    No AI is involved from here on - this just records what the operator already did."""
    card = session.get(ContentCard, card_id)
    if card is None:
        raise ValueError(f"No content card with id {card_id}")
    card.status = new_status
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def _card_for_product(session: Session, product_id: int) -> Optional[ContentCard]:
    """A product has exactly one content card once research has started."""
    statement = select(ContentCard).where(ContentCard.product_id == product_id)
    return session.exec(statement).first()
