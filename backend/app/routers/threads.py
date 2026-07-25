from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import ContentCard, ThreadsPost
from app.services.threads_pipeline import (
    get_threads_posts_for_product,
    publish_threads_post,
    run_threads_generation_task,
    select_threads_post,
    start_threads_generation,
)

router = APIRouter(prefix="/threads", tags=["threads"])


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