"""Thin client for Meta's Threads API — the only file that talks HTTP to
Threads (mirrors agents/hermes_client.py's role). Publishing is two
calls: create a container, then publish it.
https://developers.facebook.com/docs/threads/posts"""
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"

# Meta's Graph API returns transient 5xx errors on container creation
# occasionally even with a valid token and valid content - their own
# docs recommend retrying 5xx responses rather than treating the first
# one as final. 4xx errors (bad token, invalid params) are NOT retried
# since retrying can't fix those.
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 3.0


class ThreadsPublishError(Exception):
    """Carries Meta's own error message (not just the HTTP status) so
    callers can show the operator what Threads actually said - a bare
    '500 Internal Server Error for url ...' tells nobody anything
    useful about WHY it failed."""


def publish_text_post(text: str) -> str:
    container_id = _create_container(text)
    return _publish_container(container_id)


def _create_container(text: str) -> str:
    params = {"media_type": "TEXT", "text": text, "access_token": settings.threads_access_token}
    return _post_with_retry(f"{THREADS_API_BASE}/{settings.threads_user_id}/threads", params)["id"]


def _publish_container(container_id: str) -> str:
    params = {"creation_id": container_id, "access_token": settings.threads_access_token}
    return _post_with_retry(f"{THREADS_API_BASE}/{settings.threads_user_id}/threads_publish", params)["id"]


def _post_with_retry(url: str, form_data: dict) -> dict:
    """Sends as a form-encoded POST body rather than URL query params -
    the more standard way to call Graph API, and avoids the class of
    issue where a long query string (hashtags, commas, an encoded link)
    trips up proxies ahead of Meta's endpoint. Retries 5xx responses
    up to MAX_ATTEMPTS times; 4xx responses fail immediately."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = httpx.post(url, data=form_data, timeout=30.0)
        except httpx.TransportError as e:
            last_error = e
        else:
            if resp.status_code < 500:
                if resp.status_code >= 400:
                    raise _build_error(resp)
                return resp.json()
            last_error = _build_error(resp)

        if attempt < MAX_ATTEMPTS:
            logger.warning(f"[threads] attempt {attempt}/{MAX_ATTEMPTS} failed, retrying: {last_error}")
            time.sleep(RETRY_DELAY_SECONDS)

    logger.error(f"[threads] all {MAX_ATTEMPTS} attempts failed: {last_error}")
    raise last_error


def _build_error(resp: httpx.Response) -> ThreadsPublishError:
    """Meta's error body looks like {"error": {"message", "type", "code",
    "fbtrace_id"}} - extract that instead of httpx's generic message,
    which is just '500 Internal Server Error for url ...' and gives no
    clue whether this is a token problem, a content problem, or a real
    outage on Meta's side."""
    try:
        body = resp.json()
        detail = body.get("error", {}).get("message") or f"HTTP {resp.status_code} with empty error body"
        trace_id = body.get("error", {}).get("fbtrace_id", "")
    except Exception:
        detail = resp.text[:300] or f"HTTP {resp.status_code} with no body"
        trace_id = ""

    if trace_id:
        detail += f" (fbtrace_id: {trace_id})"
    return ThreadsPublishError(f"Threads API error: {detail}")