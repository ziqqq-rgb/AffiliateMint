"""
Telegram integration for the interactive scraper: shows options 5 at a
time, and lets the operator page through more, or bail out back to a
previous menu, instead of dumping every noisy OCR'd label in one
message.

Just plain HTTP calls to Telegram's Bot API - no bot framework needed
for a send + poll-for-reply flow.
"""

import math
import time

import httpx

from app.config import settings

_API_BASE = "https://api.telegram.org/bot{token}"
PAGE_SIZE = 5
_NEXT_KEYWORDS = {"next", "n"}
_BACK_KEYWORDS = {"back", "menu", "category", "categories"}


class GoBack:
    """Sentinel returned by wait_for_paginated_choice when the operator
    wants to abandon the current list and return to the previous menu
    (e.g. none of the sub-categories looked right - go pick a
    different top-level category instead)."""


class NextPage:
    """Sentinel for the lazy/incremental picker: means 'scroll for more
    and show me another page' rather than 'here is my final choice'."""


GO_BACK = GoBack()
NEXT_PAGE = NextPage()


def wait_for_one_page(
    page_items: list[str],
    allow_next: bool,
    allow_back: bool = False,
    timeout_seconds: int = 600,
) -> str | NextPage | GoBack:
    """Sends exactly the items given (already sliced by the caller) and
    waits for a number, 'next', or 'back'. Unlike wait_for_paginated_choice,
    this does NOT assume the full list is known ahead of time - use this
    when gathering more items is expensive (e.g. scrolling+OCR on a real
    device) and should only happen when the operator actually asks for
    more, not upfront for a list they might not even page through."""
    numbered = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(page_items))
    hints = []
    if allow_next:
        hints.append("'next' for more")
    if allow_back:
        hints.append("'back' for other categories")
    footer = f"\n\n(reply with a number, or {' / '.join(hints)})" if hints else ""
    _send_message(f"Pick one:\n\n{numbered}{footer}")

    deadline = time.monotonic() + timeout_seconds
    last_update_id = _get_latest_update_id()

    while time.monotonic() < deadline:
        for update in _get_updates(offset=last_update_id + 1):
            last_update_id = update["update_id"]
            text = update.get("message", {}).get("text", "").strip().lower()

            if allow_next and text in _NEXT_KEYWORDS:
                return NEXT_PAGE
            if allow_back and text in _BACK_KEYWORDS:
                return GO_BACK
            if text.isdigit():
                index = int(text) - 1
                if 0 <= index < len(page_items):
                    return page_items[index]

        time.sleep(3.0)

    raise TimeoutError(f"No valid reply on Telegram within {timeout_seconds}s.")


def wait_for_paginated_choice(
    items: list[str],
    allow_back: bool = False,
    timeout_seconds: int = 600,
) -> str | GoBack:
    """Sends `items` 5 at a time. The operator replies with:
      - a number -> picks that item on the CURRENTLY SHOWN page
      - "next"   -> shows the next page (wraps back to page 1 after the last one)
      - "back"   -> only if allow_back=True: abandons this list entirely
    Fails loudly on timeout instead of hanging forever (NFR 5.1).
    """
    total_pages = max(1, math.ceil(len(items) / PAGE_SIZE))
    page_index = 0
    _send_page(items, page_index, total_pages, allow_back)

    deadline = time.monotonic() + timeout_seconds
    last_update_id = _get_latest_update_id()

    while time.monotonic() < deadline:
        for update in _get_updates(offset=last_update_id + 1):
            last_update_id = update["update_id"]
            text = update.get("message", {}).get("text", "").strip().lower()

            if text in _NEXT_KEYWORDS:
                page_index = (page_index + 1) % total_pages
                _send_page(items, page_index, total_pages, allow_back)
                continue

            if allow_back and text in _BACK_KEYWORDS:
                return GO_BACK

            if text.isdigit():
                start = page_index * PAGE_SIZE
                page_len = min(PAGE_SIZE, len(items) - start)
                choice_on_page = int(text) - 1
                if 0 <= choice_on_page < page_len:
                    return items[start + choice_on_page]

        time.sleep(3.0)

    raise TimeoutError(f"No valid reply on Telegram within {timeout_seconds}s.")


def _send_page(items: list[str], page_index: int, total_pages: int, allow_back: bool) -> None:
    start = page_index * PAGE_SIZE
    page_items = items[start : start + PAGE_SIZE]
    numbered = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(page_items))

    hints = []
    if total_pages > 1:
        hints.append("'next' for more")
    if allow_back:
        hints.append("'back' for other categories")
    footer = f"\n\n(reply with a number, or {' / '.join(hints)})" if hints else ""

    text = f"Pick one (page {page_index + 1}/{total_pages}):\n\n{numbered}{footer}"
    _send_message(text)


def _send_message(text: str) -> None:
    httpx.post(
        f"{_API_BASE.format(token=settings.telegram_bot_token)}/sendMessage",
        json={"chat_id": settings.telegram_chat_id, "text": text},
        timeout=15.0,
    ).raise_for_status()


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