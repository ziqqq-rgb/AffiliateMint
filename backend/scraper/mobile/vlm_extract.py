"""
backend/scraper/mobile/vlm_extract.py

Replaces ocr.py's regex-based product extraction. Same contract
(screenshot bytes in, list of product dicts out) but asks a vision
model to read the cards instead of hand-tuned regex - this survives
TikTok changing "Earn RM..." to "Est. RM..." or similar wording
drift, which regex cannot.

Uses NVIDIA's NIM API (OpenAI-compatible chat completions format).
Model choice: llama-3.2-90b-vision-instruct handles OCR-style reading
of UI screenshots well. Swap MODEL if NVIDIA deprecates/renames it -
check https://build.nvidia.com for current vision model catalog.
"""

import base64
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.2-90b-vision-instruct"

PROMPT = """\
This is a screenshot of a TikTok Shop product list. Extract every product \
card visible. For each one return:
- title (string)
- price_rm (number, the item price in RM, 0 if not visible)
- commission_rm (number, the "Earn RM..." amount, 0 if not visible)
- units_sold (integer, 0 if not visible - convert "1.2K" to 1200 etc.)
- review_score (number 0-5, 0 if not visible)

Return ONLY a JSON array of objects with exactly these keys. No prose, \
no markdown fences, no explanation - just the raw JSON array.
"""


def extract_products_vlm(png_bytes: bytes) -> list[dict]:
    """Sends the screenshot to NVIDIA's vision model and returns parsed
    product dicts. Raises on bad/non-JSON output - callers should treat
    that the same as "found nothing", not silently swallow it, so a
    broken prompt or model change gets noticed instead of returning
    quietly-empty shortlists forever."""
    image_b64 = base64.b64encode(png_bytes).decode()

    response = httpx.post(
        NVIDIA_API_URL,
        headers={
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.0,  # deterministic extraction, not creative writing
        },
        timeout=30.0,
    )
    response.raise_for_status()

    raw_text = response.json()["choices"][0]["message"]["content"]
    return _parse_json_array(raw_text)


def _parse_json_array(raw_text: str) -> list[dict]:
    """Models sometimes wrap JSON in ```json fences despite instructions
    not to - strip those before parsing rather than failing on them."""
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("VLM did not return valid JSON, got: %r", raw_text[:500])
        raise


def to_scraped_product_shape(p: dict) -> dict:
    """Converts one VLM-extracted card into the dict shape
    scraper/filters.py and app/models.py expect (commission as a %,
    plus an explicit est_commission_rm). Same role ocr.py's function
    of the same name played - kept here so scrape.py only needs one
    import to switch between OCR and VLM extraction."""
    price = p.get("price_rm", 0) or 0
    commission_rm = p.get("commission_rm", 0) or 0
    return {
        "title": p.get("title", ""),
        "price_rm": price,
        "commission_percentage": round((commission_rm / price) * 100, 2) if price else 0.0,
        "est_commission_rm": commission_rm,
        "review_score": p.get("review_score", 0) or 0,
        "stock_volume": 0,  # not shown on any OCR'd/VLM'd screen we've found so far
        "units_sold": p.get("units_sold", 0) or 0,
        "product_url": "",  # neither OCR nor VLM has a URL to offer
        "raw_payload": json.dumps(p),  # keep the raw VLM read, same spirit as FR-1.4
    }