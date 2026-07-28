"""State machine for Shopee -> Threads (generate -> select -> publish),
same shape as app/services/pipeline.py but for text posts."""
from datetime import datetime, timezone

from sqlmodel import Session, select

from agents.threads_agent import generate_threads_posts
from app.db import engine
from app.models import CardStatus, ContentCard, ResearchDossier, ScrapedProduct, ThreadsPost
from app.schemas import QueuedPostOut
from app.services.pipeline import _card_for_product
from app.services.threads_client import publish_text_post
from app.services.affiliate_link import append_buy_link
from agents.memory import remember_threads_edit 



def _to_naive_utc(dt: datetime) -> datetime:
    """The frontend sends timezone-aware ISO strings (JS's
    Date.toISOString() always has a 'Z' suffix), but every datetime
    elsewhere in this app - storage, datetime.utcnow(), the scheduler's
    poll comparison - is naive UTC. Normalize once, here, so no other
    file in the pipeline has to reason about tzinfo at all."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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

    # Only one post can be "active" (selected or scheduled) per product at
    # a time - clear both flags on any sibling so publish_threads_post's
    # is_selected lookup and the scheduler's due-post query never
    # disagree about which post is "the" queued one for this product.
    siblings = session.exec(
        select(ThreadsPost).where(ThreadsPost.product_id == post.product_id, ThreadsPost.id != post.id)
    ).all()
    for sibling in siblings:
        if sibling.is_selected or sibling.scheduled_for is not None:
            sibling.is_selected = False
            sibling.scheduled_for = None
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
    """'Post this' button: publishes one post immediately - used both by
    the script card's button (post not yet selected) and the Queue
    sidebar's "Post now" (posting early, ahead of its scheduled time -
    post already selected and scheduled).

    Skips re-selecting an already-selected post: calling
    select_threads_post here unconditionally used to reset
    card.status to SCRIPT_APPROVED even when the post was still
    scheduled, so a failed publish attempt left the card showing
    "Ready to film" instead of "Queued" - misleading, since the post
    hadn't actually left the queue and the scheduler would still retry it.
    """
    post = session.get(ThreadsPost, post_id)
    if post is None:
        raise ValueError(f"No ThreadsPost with id {post_id}")

    if post.is_selected:
        card = _card_for_product(session, post.product_id)
        if card is None:
            raise ValueError(f"No ContentCard for product {post.product_id}")
    else:
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

    try:
        threads_post_id = publish_text_post(post.post_text)
    except Exception as e:
        # Record WHY it failed so the Queue sidebar / script card can
        # show it, instead of the post silently retrying every
        # scheduler tick with no visible explanation.
        post.last_publish_error = str(e)
        session.add(post)
        session.commit()
        raise

    post.threads_post_id = threads_post_id
    post.posted_at = datetime.utcnow()
    post.scheduled_for = None  # no longer "queued" once actually published
    post.last_publish_error = None
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


# --- Post Queue (schedule -> auto-publish) -------------------------------

def schedule_threads_post(session: Session, post_id: int, scheduled_for: datetime) -> ContentCard:
    """Queues a post to auto-publish at scheduled_for (app/services/
    scheduler.py polls for due posts and calls publish_threads_post).

    Enforces one post per time slot GLOBALLY (not per product) - Threads
    only has one account posting, so two products auto-firing at the
    exact same minute isn't something the queue should allow. Reuses
    select_threads_post so the "one active post per product" rule and
    its sibling-clearing stay in one place.
    """
    scheduled_for = _to_naive_utc(scheduled_for)
    if scheduled_for <= datetime.utcnow():
        raise ValueError("scheduled_for must be in the future")

    clash = session.exec(
        select(ThreadsPost).where(
            ThreadsPost.scheduled_for == scheduled_for,
            ThreadsPost.posted_at.is_(None),
            ThreadsPost.id != post_id,
        )
    ).first()
    if clash is not None:
        raise ValueError("That time slot is already taken by another queued post")

    card = select_threads_post(session, post_id)

    post = session.get(ThreadsPost, post_id)
    post.scheduled_for = scheduled_for
    session.add(post)

    card.status = CardStatus.QUEUED
    session.add(card)

    session.commit()
    session.refresh(card)
    return card


def unschedule_threads_post(session: Session, post_id: int) -> ContentCard:
    """Removes a post from the queue. The post stays selected - only its
    scheduled_for clears - since "unschedule" means "go back to manual
    posting", not "un-pick this script". Clearing scheduled_for is also
    what makes the slot reappear as choosable in list_taken_slots -
    nothing else needs to happen for the slot to "free up"."""
    post = session.get(ThreadsPost, post_id)
    if post is None:
        raise ValueError(f"No ThreadsPost with id {post_id}")

    post.scheduled_for = None
    session.add(post)

    card = _card_for_product(session, post.product_id)
    if card is not None and card.status == CardStatus.QUEUED:
        card.status = CardStatus.SCRIPT_APPROVED
        session.add(card)

    session.commit()
    if card is not None:
        session.refresh(card)
    return card


def list_queued_posts(session: Session) -> list[QueuedPostOut]:
    """Feeds the Post Queue sidebar - every scheduled-but-not-yet-posted
    post, soonest first, joined with its product/card so the sidebar
    renders a full preview without extra round-trips."""
    statement = (
        select(ThreadsPost, ScrapedProduct, ContentCard)
        .join(ScrapedProduct, ScrapedProduct.id == ThreadsPost.product_id)
        .join(ContentCard, ContentCard.product_id == ThreadsPost.product_id)
        .where(ThreadsPost.scheduled_for.is_not(None), ThreadsPost.posted_at.is_(None))
        .order_by(ThreadsPost.scheduled_for.asc())
    )
    rows = session.exec(statement).all()
    return [
        QueuedPostOut(
            post_id=post.id,
            card_id=card.id,
            product_id=product.id,
            product_title=product.title,
            product_image_url=product.image_url,
            platform=product.platform.value,
            post_text=post.post_text,
            scheduled_for=post.scheduled_for.isoformat() + "Z",
            last_publish_error=post.last_publish_error,
        )
        for post, product, card in rows
    ]


def list_taken_slots(session: Session) -> list[str]:
    """Every scheduled_for currently held by a queued (not yet posted)
    post, across all products - feeds the frontend's time-slot picker
    so it can grey out hours already claimed by another post."""
    statement = select(ThreadsPost.scheduled_for).where(
        ThreadsPost.scheduled_for.is_not(None),
        ThreadsPost.posted_at.is_(None),
    )
    return [dt.isoformat() + "Z" for dt in session.exec(statement).all()]