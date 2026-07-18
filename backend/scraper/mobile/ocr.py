"""
OCR-based product-card extraction.

TikTok's product-browsing screens render everything as images/canvas
instead of real Android text (confirmed empirically: the accessibility
tree on both the "Discover" and "Product ranking" screens has ZERO
text nodes - see scraper/mobile/README.md). That means locators can
never work here, no matter how they're tuned.

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
_MONEY_TOKEN_RE = re.compile(r"RM\s?[\dOolIS.,]+")
_OCR_DIGIT_FIXES = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "S": "5"})
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}\s")  # status bar clock, e.g. "12:22 Sat18Jul"

# Fixed UI microcopy that is plain text but NEVER a product title, even
# though it can be long enough to otherwise pass the title heuristic.
NON_TITLE_PHRASES = ("free sample", "refundable sample", "newly listed", "add")

MIN_TITLE_LENGTH = 8

# Tesseract confidence scores below this are treated as noise (stray
# pixels misread as characters), not real text.
MIN_CONFIDENCE = 25
_UPSCALE_FACTOR = 2

@dataclass
class OcrLine:
    text: str
    top: int
    left: int

NON_TITLE_PHRASES = (
    "free sample",
    "refundable sample",
    "newly listed",
    "add",
    "top selling",
    "based on cumulative",
    "sold past week",  # catches lines where the leading count got dropped
)


def _fix_money_ocr_errors(text: str) -> str:
    """Tesseract sometimes reads a digit as a similar-looking letter
    inside a money amount ('RM0.47' -> 'RMO.47'). That breaks
    PRICE_RE/EARN_RE, which then makes the line look like a fresh
    product title instead of price data. Only fix digits INSIDE 'RM...'
    tokens so real title text is never touched."""
    return _MONEY_TOKEN_RE.sub(lambda m: m.group().translate(_OCR_DIGIT_FIXES), text)

def screenshot_to_lines(png_bytes: bytes) -> list[OcrLine]:
    image = Image.open(io.BytesIO(png_bytes))
    upscaled = image.resize((image.width * _UPSCALE_FACTOR, image.height * _UPSCALE_FACTOR), Image.LANCZOS)
    data = pytesseract.image_to_data(upscaled, output_type=Output.DICT)

    lines: dict[tuple, list[tuple]] = {}
    for i, word in enumerate(data["text"]):
        if not word.strip() or int(data["conf"][i]) < MIN_CONFIDENCE:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append((word, data["left"][i], data["top"][i]))

    result = []
    for words in lines.values():
        words.sort(key=lambda w: w[1])
        result.append(
            OcrLine(
                text=_fix_money_ocr_errors(" ".join(w[0] for w in words)),
                # Divide back down to the ORIGINAL screenshot's pixel
                # space - upscaling improves OCR accuracy, but every
                # caller (tap coordinates, debug tools) expects
                # positions in the real screenshot, not the 2x version.
                top=min(w[2] for w in words) // _UPSCALE_FACTOR,
                left=min(w[1] for w in words) // _UPSCALE_FACTOR,
            )
        )

    return sorted(result, key=lambda line: line.top)   
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS) 
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
                text=_fix_money_ocr_errors(" ".join(w[0] for w in words)),
                top=min(w[2] for w in words),
                left=min(w[1] for w in words),
            )
        )

    return sorted(result, key=lambda line: line.top)


def extract_products(lines: list[OcrLine], category: str | None = None) -> list[dict]:
    """Groups OCR'd lines into product cards and pulls out the fields
    we care about with regex.

    Cards are segmented by TITLE position, not by proximity to the
    price/commission line. On this screen a card's own title sits
    further above its "Earn RMx.xx" line (~140px) than the NEXT card's
    title sits below it (~90px) - so grouping by distance from the
    price/earn line reliably grabs the wrong (next) product's title
    instead of its own. Every card has exactly one title and titles
    never overlap, so using title positions as the segment boundaries
    sidesteps that asymmetry entirely - and means no fixed pixel
    constant is needed to size the grouping window.
    """
    titles = _find_title_lines(lines, category)
    if not titles:
        return []

    cards = []
    for i, title in enumerate(titles):
        next_title_top = titles[i + 1].top if i + 1 < len(titles) else float("inf")
        card_lines = [line for line in lines if title.top <= line.top < next_title_top]
        cards.append(_parse_card(title, card_lines))
    return cards


def _find_title_lines(lines: list[OcrLine], category: str | None = None) -> list[OcrLine]:
    candidates = [
        line
        for line in lines
        if len(line.text) > MIN_TITLE_LENGTH
        and not PRICE_RE.search(line.text)
        and not EARN_RE.search(line.text)
        and not SOLD_RE.search(line.text)
        and not _TIME_RE.match(line.text)
        and not any(phrase in line.text.lower() for phrase in NON_TITLE_PHRASES)
        and (category is None or line.text.strip().lower() != category.strip().lower())
    ]
    return sorted(candidates, key=lambda line: line.top)


def _parse_card(title: OcrLine, lines: list[OcrLine]) -> dict:
    joined = " | ".join(line.text for line in lines)

    # The price line also contains an "RM" amount, and so does the
    # Earn line ("Earn RM1.99") - searching the whole joined text would
    # match the Earn line first and make price_rm equal commission_rm.
    # Only look at lines that AREN'T the earn line.
    price_line = next(
        (line for line in lines if PRICE_RE.search(line.text) and not EARN_RE.search(line.text)),
        None,
    )
    price_match = PRICE_RE.search(price_line.text) if price_line else None
    earn_match = EARN_RE.search(joined)
    sold_match = SOLD_RE.search(joined)
    rating_match = RATING_RE.search(joined)

    return {
        "title": title.text,
        "price_rm": _money_to_float(price_match.group()) if price_match else 0.0,
        "commission_rm": _money_to_float(earn_match.group()) if earn_match else 0.0,
        "units_sold": _shorthand_to_int(sold_match.group(1)) if sold_match else 0,
        "review_score": float(rating_match.group(1)) if rating_match else 0.0,
        # FR-1.4's spirit: never lose the raw read, even though it's
        # OCR text not JSON.
        "raw_ocr_text": joined,
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