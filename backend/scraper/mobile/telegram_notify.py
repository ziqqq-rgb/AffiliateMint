"""
Minimal Telegram integration: send the discovered category list as a
numbered message, then poll for the operator's reply picking one.

Just two plain HTTP calls to Telegram's Bot API - no bot framework
needed for a single send + single poll-for-reply flow.
"""

import time

import httpx

from app.config import settings

_API_BASE = "https://api.telegram.org/bot{token}"


def send_category_choices(categories: list[str]) -> None:
    numbered = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(categories))
    text = f"Pick a category to scrape - reply with its number:\n\n{numbered}"

    httpx.post(
        f"{_API_BASE.format(token=settings.telegram_bot_token)}/sendMessage",
        json={"chat_id": settings.telegram_chat_id, "text": text},
        timeout=15.0,
    ).raise_for_status()


def wait_for_category_choice(categories: list[str], timeout_seconds: int = 300) -> str:
    """Polls for a new message and returns the chosen category.
    Fails loudly on timeout instead of hanging forever (NFR 5.1)."""
    deadline = time.monotonic() + timeout_seconds
    last_update_id = _get_latest_update_id()

    while time.monotonic() < deadline:
        for update in _get_updates(offset=last_update_id + 1):
            last_update_id = update["update_id"]
            text = update.get("message", {}).get("text", "").strip()

            if text.isdigit():
                index = int(text) - 1
                if 0 <= index < len(categories):
                    return categories[index]

        time.sleep(3.0)

    raise TimeoutError(f"No valid category reply on Telegram within {timeout_seconds}s.")


def _get_latest_update_id() -> int:
    updates = _get_updates(offset=-1)
    return updates[-1]["update_id"] if updates else 0


def _get_updates(offset: int) -> list[dict]:
    response = httpx.get(
        f"{_API_BASE.format(token=settings.telegram_bot_token)}/getUpdates",
        params={"offset": offset, "timeout": 0},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["result"]