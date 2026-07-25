from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import ContentCard, ThreadsPost
from app.services.threads_pipeline import (
    get_threads_posts_for_product,
    publish_threads_post,
    select_threads_post,
    start_threads_scripting,
)

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("/{dossier_id}/generate", response_model=list[ThreadsPost])
def generate(dossier_id: int, session: Session = Depends(get_session)):
    try:
        return start_threads_scripting(session, dossier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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