"""
Vision-based product extraction using NVIDIA's API (NIM) - alternative
to ocr.py's OCR+regex approach.

Sends the raw screenshot to a vision model and asks for structured
JSON back directly, instead of reading pixels with Tesseract and
regexing the result. Same input/output shape as ocr.py's
extract_products(), so scrape.py can swap between them with one line.
"""

import base64
import io
import json

import httpx
from PIL import Image

from app.config import settings

EXTRACTION_PROMPT = """\
This is a screenshot of a TikTok Shop product listing screen.
List every product card visible.

Each card has TWO different RM amounts - do not mix them up:
1. commission_rm: the smaller amount next to the word "Earn" (e.g. "Earn RM0.90" -> commission_rm is 0.90)
2. price_rm: the larger amount below it, the actual selling price (e.g. "RM8.99" -> price_rm is 8.99).
   If there's a crossed-out price next to it, ignore the crossed-out one and use the non-crossed-out price.

Example: if a card shows "Earn RM0.90" and "RM8.99 RM12.00", then:
  commission_rm = 0.90
  price_rm = 8.99   (NOT 0.90 - commission_rm and price_rm are almost never the same number)

For each product also give:
- title (string)
- units_sold (number, convert "23.2K sold" to 23200)
- review_score (number, 0 if no star rating is shown)

Ignore anything that isn't a product card (headers, filter tabs, status bar).
Return ONLY a JSON array. No explanation, no markdown formatting.
"""

def _resize_for_upload(png_bytes: bytes, max_width: int = 800) -> bytes:
    """Shrinks the screenshot before sending - full-res phone
    screenshots are unnecessarily large for OCR-style text reading,
    and a smaller payload uploads faster and times out less."""
    image = Image.open(io.BytesIO(png_bytes))
    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, int(image.height * ratio)), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def extract_products_with_ai(png_bytes: bytes) -> list[dict]:
    resized = _resize_for_upload(png_bytes)
    image_b64 = base64.b64encode(resized).decode()

    try:
        response = httpx.post(
            f"{settings.nvidia_api_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
            json={
                "model": settings.nvidia_vision_model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }],
                "max_tokens": 2000,
                "temperature": 0.0,
            },
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0),
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise RuntimeError(
            "NVIDIA API request timed out. Check: (1) NVIDIA_API_KEY is set and valid, "
            "(2) nvidia_api_url/model name in config.py are correct, "
            "(3) your network can reach integrate.api.nvidia.com."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"NVIDIA API returned {e.response.status_code}: {e.response.text[:300]}")

    raw_text = response.json()["choices"][0]["message"]["content"]
    return _parse_json_response(raw_text)


def _parse_json_response(raw_text: str) -> list[dict]:
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)