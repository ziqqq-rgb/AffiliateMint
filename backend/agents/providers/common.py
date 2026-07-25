"""
Shared helpers for LLM provider clients.

Every provider (Hermes, NVIDIA, Gemini) needs the same two things: strip
markdown fences the model sometimes adds despite instructions, and retry
a couple times on malformed JSON. Centralizing it here means each client
below only has to implement its own HTTP call.
"""
import json
import re
from typing import Any, Callable
import httpx


MAX_JSON_RETRIES = 2


def strip_json_fences(content: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()


def run_with_json_retry(call: Callable[[], str], expects_json: bool) -> Any:
    """Calls `call()` up to MAX_JSON_RETRIES+1 times. Only retries on
    malformed JSON - network/auth errors from `call()` propagate immediately,
    since retrying those just burns quota for no reason."""
    for attempt in range(MAX_JSON_RETRIES + 1):
        content = call()
        if not expects_json:
            return content
        try:
            return json.loads(strip_json_fences(content))
        except json.JSONDecodeError as e:
            if attempt == MAX_JSON_RETRIES:
                raise
            print(f"[WARN] Malformed JSON on attempt {attempt + 1}: {e}")

MAX_TRANSIENT_RETRIES = 1

def call_with_retry(call: Callable[[], str]) -> str:
    """Retries once on timeouts/connection errors - these happen
    routinely with LLM providers under load and aren't the request's
    fault, unlike a 4xx which should fail immediately."""
    for attempt in range(MAX_TRANSIENT_RETRIES + 1):
        try:
            return call()
        except (httpx.TimeoutException, httpx.TransportError) as e:
            if attempt == MAX_TRANSIENT_RETRIES:
                raise
            print(f"[WARN] Transient network error (attempt {attempt + 1}): {e}")