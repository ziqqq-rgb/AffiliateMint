from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ContentCard, ThreadsPost
from app.schemas import QueuedPostOut
from app.services.threads_pipeline import (
    edit_threads_post,
    get_threads_posts_for_product,
    list_queued_posts,
    post_threads_post_now,
    publish_threads_post,
    run_threads_generation_task,
    schedule_threads_post,
    select_threads_post,
    start_threads_generation,
    unschedule_threads_post,
)

router = APIRouter(prefix="/threads", tags=["threads"])


class ThreadsPostUpdateRequest(BaseModel):
    post_text: str


class ScheduleRequest(BaseModel):
    scheduled_for: datetime


@router.post("/{dossier_id}/generate", response_model=ContentCard)
def generate(dossier_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """Returns immediately; poll GET /threads/product/{id} or
    GET /cards/{id} (watch is_generating) for when posts are ready -
    same pattern as products.py's run-pipeline endpoint."""
    try:
        card = start_threads_generation(session, dossier_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    background_tasks.add_task(run_threads_generation_task, dossier_id)
    return card


@router.post("/posts/{post_id}/select", response_model=ContentCard)
def select(post_id: int, session: Session = Depends(get_session)):
    try:
        return select_threads_post(session, post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{card_id}/publish", response_model=ContentCard)
def publish(card_id: int, session: Session = Depends(get_session)):
    try:
        return publish_threads_post(session, card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/product/{product_id}", response_model=list[ThreadsPost])
def list_for_product(product_id: int, session: Session = Depends(get_session)):
    return get_threads_posts_for_product(session, product_id)

@router.put("/posts/{post_id}", response_model=ThreadsPost)
def update(post_id: int, body: ThreadsPostUpdateRequest, session: Session = Depends(get_session)):
    """Hand-edit a post's text - mirrors scripts.py's PUT /scripts/{id}."""
    try:
        return edit_threads_post(session, post_id, body.post_text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/posts/{post_id}/post-now", response_model=ContentCard)
def post_now(post_id: int, session: Session = Depends(get_session)):
    """'Post this' button: selects + publishes this post immediately."""
    try:
        return post_threads_post_now(session, post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/posts/{post_id}/schedule", response_model=ContentCard)
def schedule(post_id: int, body: ScheduleRequest, session: Session = Depends(get_session)):
    """Post Queue: schedule this post to auto-publish at scheduled_for."""
    try:
        return schedule_threads_post(session, post_id, body.scheduled_for)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/unschedule", response_model=ContentCard)
def unschedule(post_id: int, session: Session = Depends(get_session)):
    try:
        return unschedule_threads_post(session, post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/queue", response_model=list[QueuedPostOut])
def queue(session: Session = Depends(get_session)):
    """Feeds the Post Queue sidebar."""
    return list_queued_posts(session)