"""
Low-level client for the Hermes Agent (Nous Research).

This is the ONLY file that knows how to actually talk to Hermes -
research_agent.py and script_agent.py both call `run_task()` and
never touch HTTP/auth details directly. Swapping the reasoning engine
later means changing this one file.
"""

import json
from typing import Any
import re
import httpx

from app.config import settings


def run_task(prompt: str, expects_json: bool = False):
    payload = {
        "model": "default",
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant. Always output strictly valid JSON without markdown formatting." if expects_json else "You are a helpful AI assistant."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {getattr(settings, 'hermes_api_key', 'local-dev-key')}"
    }

    response = httpx.post(
        f"{settings.hermes_api_url}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"].strip()
    
    # If the caller expects JSON, parse the string into a Python dictionary!
    if expects_json:
        # Strip markdown code blocks (e.g., ```json ... ```) just in case the LLM added them
        cleaned_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM JSON: {cleaned_content}")
            raise e
            
    return content