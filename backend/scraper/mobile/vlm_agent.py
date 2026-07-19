"""
backend/scraper/mobile/vlm_agent.py

VLM-driven screen understanding for mobile navigation - replaces
categories.py's OCR+regex clustering (discover_top_tabs,
discover_sub_categories, the fuzzy-match re-find logic) with direct
vision-model reads. The model understands "this is a tappable
category label" as a concept, so it survives TikTok changing layout
or wording that broke regex-based clustering.

Same NVIDIA NIM setup as vlm_extract.py (kept as a separate file since
the prompts/return shapes are different - one extracts product data,
this one finds tap targets).
"""

import base64
import io
import json
import logging
import time

import httpx
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-nano-12b-v2-vl"
REQUEST_TIMEOUT = httpx.Timeout(connect=10.0, read=150.0, write=10.0, pool=10.0)
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 3.0
MAX_UPLOAD_DIMENSION = 768

TOP_TABS_PROMPT = """\
This is a screenshot of a TikTok Shop "Product Ranking" screen, {width}x{height}px. \
Find the horizontal row of category tabs near the top (e.g. "For You", \
"Food & Beverages", "Pet Supplies"). Ignore the status bar (clock/battery) \
and the page's own title text.

For each tab, give its visible text and the pixel coordinates of its center.

Return ONLY a JSON array like:
[{{"text": "Food & Beverages", "x": 240, "y": 96}}]
No prose, no markdown fences.
"""

SUB_CATEGORIES_PROMPT = """\
This is a screenshot of a TikTok Shop category screen, {width}x{height}px. \
Find every section on this screen. Each section has a bold heading (e.g. \
"Candy", "Dried Foods") followed by a small link like "2 new products >".

Return the HEADING text, not the link text - "Candy", never "2 new products".
The tap coordinates should be the link's position (the "N new products" text), \
not the heading's position.

Return ONLY a JSON array like:
[{{"text": "Candy", "x": 180, "y": 512}}]
No prose, no markdown fences.
"""

FIND_LABEL_PROMPT = """\
This is a screenshot, {width}x{height}px. Is text matching "{label}" visible \
anywhere on screen? Minor differences (spacing, "&" vs "and", a dropped word) \
still count as a match.

Return ONLY JSON: {{"found": true, "x": 180, "y": 512}} or {{"found": false}}
No prose, no markdown fences.
"""


def get_image_size(png_bytes: bytes) -> tuple[int, int]:
    image = Image.open(io.BytesIO(png_bytes))
    return image.width, image.height


def _resize_for_upload(png_bytes: bytes) -> tuple[bytes, float, int, int]:
    """Downscales the screenshot if it's bigger than MAX_UPLOAD_DIMENSION.
    Returns (resized_bytes, scale_factor, resized_width, resized_height) -
    scale_factor converts a coordinate the model gives us (in the resized
    image) back to the real screen's pixel coordinates for tapping."""
    image = Image.open(io.BytesIO(png_bytes))
    longest_side = max(image.width, image.height)

    if longest_side <= MAX_UPLOAD_DIMENSION:
        return png_bytes, 1.0, image.width, image.height

    scale_factor = longest_side / MAX_UPLOAD_DIMENSION
    new_size = (round(image.width / scale_factor), round(image.height / scale_factor))
    resized = image.resize(new_size, Image.LANCZOS)

    buffer = io.BytesIO()
    resized.save(buffer, format="PNG")
    return buffer.getvalue(), scale_factor, new_size[0], new_size[1]


def discover_top_tabs_vlm(png_bytes: bytes) -> list[dict]:
    """Returns [{"text": ..., "x": ..., "y": ...}] for the category tab row,
    coordinates already scaled to the ORIGINAL screenshot's pixels."""
    resized_bytes, scale, width, height = _resize_for_upload(png_bytes)
    prompt = TOP_TABS_PROMPT.format(width=width, height=height)
    result = _call_vlm(resized_bytes, prompt)
    labels = result if isinstance(result, list) else []
    return [_scale_label(label, scale) for label in labels]


def discover_sub_categories_vlm(png_bytes: bytes) -> list[dict]:
    """Returns [{"text": ..., "x": ..., "y": ...}] for tappable section links,
    coordinates already scaled to the ORIGINAL screenshot's pixels."""
    resized_bytes, scale, width, height = _resize_for_upload(png_bytes)
    prompt = SUB_CATEGORIES_PROMPT.format(width=width, height=height)
    result = _call_vlm(resized_bytes, prompt)
    labels = result if isinstance(result, list) else []
    return [_scale_label(label, scale) for label in labels]


def find_label_vlm(png_bytes: bytes, label_text: str) -> dict | None:
    """Asks the VLM whether `label_text` is visible on the current screen.
    Returns {"x": int, "y": int} (scaled to the ORIGINAL screenshot) if
    found, else None."""
    resized_bytes, scale, width, height = _resize_for_upload(png_bytes)
    prompt = FIND_LABEL_PROMPT.format(width=width, height=height, label=label_text)
    result = _call_vlm(resized_bytes, prompt)
    if isinstance(result, dict) and result.get("found"):
        return {"x": round(result["x"] * scale), "y": round(result["y"] * scale)}
    return None


def _scale_label(label: dict, scale: float) -> dict:
    return {"text": label["text"], "x": round(label["x"] * scale), "y": round(label["y"] * scale)}


def _call_vlm(png_bytes: bytes, prompt: str):
    """Single retrying call to the NVIDIA vision model. Raises on repeated
    failure - callers should treat that as "couldn't read this screen",
    not silently proceed as if nothing were there."""
    image_b64 = base64.b64encode(png_bytes).decode()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
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
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                            ],
                        }
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.0,
                    "chat_template_kwargs": {"thinking": False},  # NEW: we just want the JSON, not a reasoning trace
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            raw_text = response.json()["choices"][0]["message"]["content"]
            return _parse_json(raw_text)

        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            last_error = exc
            logger.warning("VLM agent call failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)

    raise RuntimeError(f"VLM agent call failed after {MAX_RETRIES} attempts") from last_error


def _parse_json(raw_text: str | None):
    """Models sometimes wrap JSON in ```json fences despite instructions
    not to - strip those before parsing rather than failing on them."""
    if not raw_text:
        raise RuntimeError("VLM returned empty content (likely ran out of tokens on reasoning - check chat_template_kwargs/max_tokens)")
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("VLM agent did not return valid JSON, got: %r", raw_text[:500])
        raise