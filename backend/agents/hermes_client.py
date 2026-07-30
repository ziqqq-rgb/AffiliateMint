"""
Hermes Agent client - local memory/learning model (agents/memory.py's
FTS5 ledger sits alongside this). Same JSON-retry contract as the other
providers (agents/providers/*_client.py), so it reuses their shared
retry helper instead of re-implementing it.
"""
import httpx

from agents.providers.common import run_with_json_retry
from app.config import settings


def run_task(prompt: str, expects_json: bool = False):
    """No transient-network retry wrapper here (unlike the nvidia/gemini
    clients) - Hermes runs locally, so a connection failure almost
    always means the local server isn't up, not a fluke worth retrying."""
    return run_with_json_retry(lambda: _call_hermes(prompt, expects_json), expects_json)


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
