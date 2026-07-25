"""State machine for Shopee -> Threads (generate -> select -> publish),
same shape as app/services/pipeline.py but for text posts."""
from datetime import datetime

from sqlmodel import Session, select

from agents.threads_agent import generate_threads_posts
from app.db import engine
from app.models import CardStatus, ContentCard, ResearchDossier, ScrapedProduct, ThreadsPost
from app.services.pipeline import _card_for_product
from app.services.threads_client import publish_text_post
from app.services.affiliate_link import append_buy_link



def start_threads_generation(session: Session, dossier_id: int) -> ContentCard:
    """Flips the `is_generating` lock and returns immediately - same guard
    as pipeline.start_full_pipeline. The actual Gemini call happens in
    run_threads_generation_task, off the request thread, since it can run
    longer than an HTTP client is willing to wait."""
    dossier = session.get(ResearchDossier, dossier_id)
    if dossier is None:
        raise ValueError(f"No ResearchDossier with id {dossier_id}")

    card = _card_for_product(session, dossier.product_id)
    if card is None:
        raise ValueError(f"No ContentCard for product {dossier.product_id}")
    if card.is_generating:
        raise ValueError("Threads post generation is already running for this product")

    card.is_generating = True
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def run_threads_generation_task(dossier_id: int) -> None:
    """Runs off the request thread - opens its own DB session since the
    request's session is gone by the time a background task executes."""
    with Session(engine) as session:
        dossier = session.get(ResearchDossier, dossier_id)
        if dossier is None:
            return
        card = _card_for_product(session, dossier.product_id)
        if card is None:
            return

        try:
            product = session.get(ScrapedProduct, dossier.product_id)
            posts = [
                ThreadsPost(product_id=dossier.product_id, post_text=append_buy_link(text, product))
                for text in generate_threads_posts(dossier)
            ]
            session.add_all(posts)
            card.status = CardStatus.SCRIPTED_PENDING
        finally:
            card.is_generating = False
            session.add(card)
            session.commit()


def select_threads_post(session: Session, post_id: int) -> ContentCard:
    post = session.get(ThreadsPost, post_id)
    if post is None:
        raise ValueError(f"No ThreadsPost with id {post_id}")

    post.is_selected = True
    session.add(post)

    card = _card_for_product(session, post.product_id)
    card.status = CardStatus.SCRIPT_APPROVED
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def publish_threads_post(session: Session, card_id: int) -> ContentCard:
    card = session.get(ContentCard, card_id)
    if card is None:
        raise ValueError(f"No ContentCard with id {card_id}")

    post = session.exec(
        select(ThreadsPost).where(ThreadsPost.product_id == card.product_id, ThreadsPost.is_selected == True)
    ).first()
    if post is None:
        raise ValueError("No selected Threads post for this card")

    # post_text already has the buy link - no more double-appending here
    post.threads_post_id = publish_text_post(post.post_text)
    post.posted_at = datetime.utcnow()
    session.add(post)

    card.status = CardStatus.POSTED
    card.posted_at = datetime.utcnow()
    session.add(card)

    session.commit()
    session.refresh(card)
    return card

def get_threads_posts_for_product(session: Session, product_id: int) -> list[ThreadsPost]:
    """Feeds the card-detail view, same role as pipeline.get_scripts_for_product."""
    statement = select(ThreadsPost).where(ThreadsPost.product_id == product_id)
    return list(session.exec(statement))

def auto_select_and_publish(session: Session, posts: list[ThreadsPost]) -> ContentCard:
    """Skips manual review — picks the first generated variant and
    publishes it immediately. Used by the one-click pipeline when
    auto-publish is enabled."""
    card = select_threads_post(session, posts[0].id)
    return publish_threads_post(session, card.id)