import json
import re
from typing import Any

import httpx

from app.config import settings

MAX_JSON_RETRIES = 2  


def run_task(prompt: str, expects_json: bool = False):
    for attempt in range(MAX_JSON_RETRIES + 1):
        content = _call_hermes(prompt, expects_json)
        if not expects_json:
            return content

        try:
            return _parse_json_response(content)
        except json.JSONDecodeError as e:
            is_last_attempt = attempt == MAX_JSON_RETRIES
            print(f"[WARN] Malformed JSON on attempt {attempt + 1}: {e}")
            if is_last_attempt:
                raise


def _call_hermes(prompt: str, expects_json: bool) -> str:
    payload = {
        "model": "default",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. Always output strictly valid JSON "
                    "without markdown formatting."
                    if expects_json else "You are a helpful AI assistant."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        # Lower temperature when strict JSON is expected - less room for
        # the syntax slip-ups that free-form creativity introduces.
        "temperature": 0.3 if expects_json else 0.7,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {getattr(settings, 'hermes_api_key', 'local-dev-key')}",
    }

    response = httpx.post(
        f"{settings.hermes_api_url}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _parse_json_response(content: str) -> Any:
    """Strips markdown code fences the LLM sometimes adds despite
    instructions, then parses. Raises JSONDecodeError untouched so the
    caller (run_task) can decide whether to retry."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
    return json.loads(cleaned)