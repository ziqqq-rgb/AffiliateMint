"""
Discovers every category section on the Product Ranking screen.

Crops out the top ~20% of each screenshot before sending it to the
vision model - that region is the fixed tab bar (For You, Pet
Supplies, Home Improvement...), which is navigation chrome, not a
real section heading. Without the crop, the model mixes tab-bar
labels in with genuine headings, which is what caused categories to
appear out of order and duplicated last time.
"""

import base64
import io
import json

import httpx
from PIL import Image

from app.config import settings
from scraper.mobile import navigate
from scraper.mobile.driver import human_delay

CATEGORY_PROMPT = """\
This is the PRODUCT section of TikTok Shop's "Product ranking" screen
(navigation chrome has already been removed). List every category
heading visible (e.g. "Instant Hijab", "Tea") - each sits directly
above a row of product cards. Do not include "Top selling" badges or
individual product titles.

Return ONLY a JSON array of short strings, nothing else - no
explanation, no markdown formatting, no trailing commentary.
If none are visible, return [].
"""

_CROP_TOP_FRACTION = 0.20  # tune if TikTok's header height changes


def discover_categories(driver, max_scrolls: int = 12) -> tuple[list[str], int]:
    """Returns (categories found, number of scrolls performed) - the
    scroll count lets the caller scroll back up by the same amount
    afterward instead of guessing."""
    seen: list[str] = []
    scrolls_done = 0

    for _ in range(max_scrolls):
        found = _extract_categories(driver.get_screenshot_as_png())
        new_ones = [c for c in found if c not in seen]
        if not new_ones:
            break

        seen.extend(new_ones)
        navigate.scroll_down(driver)
        human_delay()
        scrolls_done += 1

    return seen, scrolls_done


def _crop_tab_bar(png_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(png_bytes))
    cropped = image.crop((0, int(image.height * _CROP_TOP_FRACTION), image.width, image.height))
    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG")
    return buffer.getvalue()


# backend/scraper/mobile/categories.py

def _extract_categories(png_bytes: bytes) -> list[str]:
    cropped = _crop_tab_bar(png_bytes)
    image_b64 = base64.b64encode(cropped).decode()

    response = httpx.post(
        f"{settings.nvidia_api_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
        json={
            "model": settings.nvidia_vision_model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": CATEGORY_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            }],
            "max_tokens": 1500,  # was 500 - too small, was truncating the JSON mid-string
            "temperature": 0.0,
        },
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0),
    )
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"]
    return _parse_category_response(raw_text)


def _parse_category_response(raw_text: str) -> list[str]:
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Fail with the actual text the model sent back, not just a
        # generic parse error - makes it obvious at a glance whether
        # this was truncation, a stray comment, or something else.
        raise RuntimeError(
            f"Model returned invalid JSON for category list: {e}\n"
            f"Raw response was:\n{raw_text!r}"
        )