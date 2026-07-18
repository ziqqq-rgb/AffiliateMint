"""
OCR-based product-card extraction.

TikTok's product-browsing screens render everything as images/canvas
instead of real Android text (confirmed empirically: the accessibility
tree on both the "Discover" and "Product ranking" screens has ZERO
text nodes - see scraper/mobile/README.md). That means locators
(the original plan in locators.py/scrape.py) can never work here,
no matter how they're tuned.

This reads the screen the way a person would instead: take a
screenshot, run text recognition on the actual pixels, then group the
words it finds into rows and pull out price/commission/sold with
regex. It's a best-effort reconstruction, not a clean data feed.
"""

import io
import re
from dataclasses import dataclass

import pytesseract
from PIL import Image
from pytesseract import Output

PRICE_RE = re.compile(r"RM\s?[\d,]+\.\d{2}")
EARN_RE = re.compile(r"Earn\s+RM\s?[\d,]+\.\d{2}", re.IGNORECASE)
SOLD_RE = re.compile(r"([\d.,]+K?)\s*sold", re.IGNORECASE)
RATING_RE = re.compile(r"(\d\.\d)\s*\(([\d.,]+K?)\)")

# How close two OCR'd lines need to be vertically (in pixels) to be
# treated as part of the same product card. TUNE THIS if cards are
# getting merged together or split apart on your screen resolution.
ROW_GROUPING_PX = 140

# Tesseract drops confidence scores below this are treated as noise
# (stray pixels misread as characters), not real text.
MIN_CONFIDENCE = 40


@dataclass
class OcrLine:
    text: str
    top: int
    left: int


def screenshot_to_lines(png_bytes: bytes) -> list[OcrLine]:
    """Runs OCR on a screenshot and reconstructs it into lines of text
    with their on-screen position, using Tesseract's own line grouping
    (block/paragraph/line numbers) rather than re-inventing clustering.
    """
    image = Image.open(io.BytesIO(png_bytes))
    data = pytesseract.image_to_data(image, output_type=Output.DICT)

    lines: dict[tuple, list[tuple]] = {}
    for i, word in enumerate(data["text"]):
        if not word.strip() or int(data["conf"][i]) < MIN_CONFIDENCE:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append((word, data["left"][i], data["top"][i]))

    result = []
    for words in lines.values():
        words.sort(key=lambda w: w[1])  # left-to-right within the line
        result.append(
            OcrLine(
                text=" ".join(w[0] for w in words),
                top=min(w[2] for w in words),
                left=min(w[1] for w in words),
            )
        )

    return sorted(result, key=lambda l: l.top)


def extract_products(lines: list[OcrLine]) -> list[dict]:
    """Groups OCR'd lines into product cards and pulls out the fields
    we care about with regex.

    Every card needs a price ("RM14.88") or an earn line ("Earn
    RM2.73") to be counted - that's the anchor everything else in the
    card gets grouped around by vertical proximity.

    TODO: title extraction is a rough guess (longest non-numeric line
    near the anchor) - improve this if you need clean product names.
    """
    anchors = [l for l in lines if PRICE_RE.search(l.text) or EARN_RE.search(l.text)]
    cards = [_parse_card([l for l in lines if abs(l.top - anchor.top) <= ROW_GROUPING_PX]) for anchor in anchors]

    # A card with both a price line and an earn line gets anchored twice
    # (once per line) and produces two identical entries - keep one.
    seen = set()
    deduped = []
    for card in cards:
        key = card["raw_ocr_text"]
        if key not in seen:
            seen.add(key)
            deduped.append(card)
    return deduped


def _parse_card(lines: list[OcrLine]) -> dict:
    joined = " | ".join(l.text for l in lines)

    price_match = PRICE_RE.search(joined)
    earn_match = EARN_RE.search(joined)
    sold_match = SOLD_RE.search(joined)
    rating_match = RATING_RE.search(joined)

    title_candidates = [
        l.text
        for l in lines
        if not PRICE_RE.search(l.text)
        and not EARN_RE.search(l.text)
        and not SOLD_RE.search(l.text)
        and len(l.text) > 8
    ]
    title = max(title_candidates, key=len) if title_candidates else ""

    return {
        "title": title,
        "price_rm": _money_to_float(price_match.group()) if price_match else 0.0,
        "commission_rm": _money_to_float(earn_match.group()) if earn_match else 0.0,
        "units_sold": _shorthand_to_int(sold_match.group(1)) if sold_match else 0,
        "review_score": float(rating_match.group(1)) if rating_match else 0.0,
        "raw_ocr_text": joined,  # FR-1.4's spirit: never lose the raw read, even though it's OCR text not JSON
    }


def _money_to_float(text: str) -> float:
    digits = re.sub(r"[^\d.]", "", text)
    try:
        return float(digits)
    except ValueError:
        return 0.0


def _shorthand_to_int(text: str) -> int:
    text = text.strip().upper()
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1_000)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        return int(float(re.sub(r"[^\d.]", "", text)))
    except ValueError:
        return 0
