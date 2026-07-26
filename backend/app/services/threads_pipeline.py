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
from agents.memory import remember_threads_edit 



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

    # Only one post can be selected per product at a time - unselect any
    # previous pick so publish_threads_post's is_selected lookup is unambiguous.
    siblings = session.exec(
        select(ThreadsPost).where(ThreadsPost.product_id == post.product_id, ThreadsPost.id != post.id)
    ).all()
    for sibling in siblings:
        if sibling.is_selected:
            sibling.is_selected = False
            session.add(sibling)

    post.is_selected = True
    session.add(post)

    card = _card_for_product(session, post.product_id)
    card.status = CardStatus.SCRIPT_APPROVED
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def edit_threads_post(session: Session, post_id: int, post_text: str) -> ThreadsPost:
    """Hand-edit a generated Threads post - Threads analogue of
    app/services/pipeline.py's edit_script. Feeds the edit into Hermes'
    memory so future posts lean toward kept phrasing (same feedback
    loop as script edits)."""
    post = session.get(ThreadsPost, post_id)
    if post is None:
        raise ValueError(f"No ThreadsPost with id {post_id}")
    if post.posted_at is not None:
        raise ValueError("Cannot edit a post that has already been published")

    post.post_text = post_text
    session.add(post)
    session.commit()
    session.refresh(post)

    remember_threads_edit(post)
    return post


def post_threads_post_now(session: Session, post_id: int) -> ContentCard:
    """'Post this' button: selects and publishes one post in a single
    action. Also used by auto_select_and_publish below."""
    card = select_threads_post(session, post_id)
    return publish_threads_post(session, card.id)


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
    """Skips manual review - picks the first generated variant and
    publishes it immediately. Used by the one-click pipeline when
    auto-publish is enabled."""
    return post_threads_post_now(session, posts[0].id)