"""
NVIDIA NIM client - hosts third-party models (Z.ai's GLM-5.2) behind an
OpenAI-compatible /chat/completions endpoint. Used by the research agent.

Thinking is explicitly disabled: GLM-5.2 reasons by default, but a
research dossier is a plain JSON extraction task, not a task that
benefits from deep reasoning on a 753B model - leaving thinking on would
just add latency and cost for no quality gain here.
"""
import httpx

from agents.providers.common import call_with_retry, run_with_json_retry
from app.config import settings

TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)

def run_task(prompt: str, expects_json: bool = False):
    def _call() -> str:
        response = httpx.post(
            settings.nvidia_api_base,
            json={
                "model": settings.nvidia_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful AI assistant. Always output strictly "
                            "valid JSON without markdown formatting."
                            if expects_json else "You are a helpful AI assistant."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3 if expects_json else 0.7,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.nvidia_api_key}",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    return run_with_json_retry(lambda: call_with_retry(_call), expects_json)