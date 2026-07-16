"""
Low-level client for the Hermes Agent (Nous Research).

This is the ONLY file that knows how to actually talk to Hermes -
research_agent.py and script_agent.py both call `run_task()` and
never touch HTTP/auth details directly. Swapping the reasoning engine
later means changing this one file.
"""

import json
from typing import Any

import httpx

from app.config import settings


def run_task(prompt: str, expects_json: bool = True) -> Any:
    """Send one single-purpose task to Hermes and return its output.

    Hermes runs each request as a single-purpose task, not an
    open-ended chat (design doc 3.2 - "Deterministic execution"), so
    the response is expected to be tightly-scoped JSON when
    `expects_json` is True.
    """
    response = httpx.post(
        f"{settings.hermes_api_url}/v1/tasks",
        headers={"Authorization": f"Bearer {settings.hermes_api_key}"},
        json={"prompt": prompt},
        timeout=60.0,
    )
    response.raise_for_status()
    output = response.json()["output"]
    return json.loads(output) if expects_json else output
