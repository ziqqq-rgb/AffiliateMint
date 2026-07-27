"""
Polling scheduler for queued Threads posts (Post Queue feature).

No cron/task-queue dependency: a single asyncio loop started at FastAPI
startup, checking every POLL_INTERVAL_SECONDS for ThreadsPost rows whose
scheduled_for has passed. For a single-instance, solo-operated app this
is simpler than adding APScheduler/Celery - and since it queries by
absolute due-time rather than firing a one-shot timer, a missed tick
(server restart, brief downtime) is self-healing: the next poll just
finds the same still-due row and publishes it late, nothing is lost.
"""
import asyncio
import logging
from datetime import datetime

from sqlmodel import Session, select

from app.db import engine
from app.models import ThreadsPost
from app.services.pipeline import _card_for_product
from app.services.threads_pipeline import publish_threads_post

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


async def run_scheduler_loop() -> None:
    """Runs forever as a background task (see main.py's startup event) -
    never raises, so one bad tick can't kill the whole loop."""
    while True:
        try:
            _publish_due_posts()
        except Exception as e:
            logger.error(f"[scheduler] tick failed: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def _publish_due_posts() -> None:
    with Session(engine) as session:
        due_posts = session.exec(
            select(ThreadsPost).where(
                ThreadsPost.scheduled_for.is_not(None),
                ThreadsPost.scheduled_for <= datetime.utcnow(),
                ThreadsPost.posted_at.is_(None),
            )
        ).all()

        for post in due_posts:
            card = _card_for_product(session, post.product_id)
            if card is None:
                logger.warning(f"[scheduler] No card for product {post.product_id}, skipping post {post.id}")
                continue
            try:
                publish_threads_post(session, card.id)
                logger.info(f"[scheduler] Published queued post {post.id} (product {post.product_id})")
            except Exception as e:
                logger.error(f"[scheduler] Failed to publish post {post.id}: {e}")