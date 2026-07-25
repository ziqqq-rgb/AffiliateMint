"""
Google AI Studio (Gemini API) client. Used by the script agent.

Uses generationConfig.responseMimeType for JSON mode instead of relying
on prompt instructions alone - more reliable than hoping the model
follows a "return JSON" instruction in plain text.

No temperature/top_p/top_k: Gemini 3.x deprecates sampling params -
the API ignores or rejects them, so this client doesn't send them.
"""
import httpx

from agents.providers.common import call_with_retry, run_with_json_retry
from app.config import settings

TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


def run_task(prompt: str, expects_json: bool = False):
    def _call() -> str:
        url = f"{settings.gemini_api_base}/{settings.gemini_model}:generateContent"
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        if expects_json:
            body["generationConfig"] = {"responseMimeType": "application/json"}

        response = httpx.post(url, params={"key": settings.gemini_api_key}, json=body, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    return run_with_json_retry(lambda: call_with_retry(_call), expects_json)