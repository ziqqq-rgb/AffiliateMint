"""Thin client for Meta's Threads API — the only file that talks HTTP to
Threads (mirrors agents/hermes_client.py's role). Publishing is two
calls: create a container, then publish it.
https://developers.facebook.com/docs/threads/posts"""
import httpx

from app.config import settings

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def publish_text_post(text: str) -> str:
    container_id = _create_container(text)
    return _publish_container(container_id)


def _create_container(text: str) -> str:
    resp = httpx.post(
        f"{THREADS_API_BASE}/{settings.threads_user_id}/threads",
        params={"media_type": "TEXT", "text": text, "access_token": settings.threads_access_token},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _publish_container(container_id: str) -> str:
    resp = httpx.post(
        f"{THREADS_API_BASE}/{settings.threads_user_id}/threads_publish",
        params={"creation_id": container_id, "access_token": settings.threads_access_token},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["id"]