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
_MONEY_TOKEN_RE = re.compile(r"RM\s?[\dOolIS.,]+")
_OCR_DIGIT_FIXES = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "S": "5"})

MIN_TITLE_LENGTH = 25

# Tesseract confidence scores below this are treated as noise (stray
# pixels misread as characters), not real text.
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
        and (category is None or line.text.strip().lower() != category.strip().lower())
    ]
    return sorted(candidates, key=lambda line: line.top)


def _parse_card(title: OcrLine, lines: list[OcrLine]) -> dict:
    fixed_lines = [_fix_money_ocr_errors(line.text) for line in lines]
    space_joined = " ".join(fixed_lines)  # lets "Earn" + "RM1.99" match even if OCR split them onto two lines

    # The price line also contains an "RM" amount, and so does the
    # Earn line ("Earn RM1.99") - searching the whole joined text would
    # match the Earn line first and make price_rm equal commission_rm.
    # Only look at individual lines that AREN'T the earn line.
    price_match = None
    for fixed_text in fixed_lines:
        if PRICE_RE.search(fixed_text) and not EARN_RE.search(fixed_text):
            price_match = PRICE_RE.search(fixed_text)
            break

    earn_match = EARN_RE.search(space_joined)
    sold_match = SOLD_RE.search(space_joined)
    rating_match = RATING_RE.search(space_joined)

    price_rm = _money_to_float(price_match.group()) if price_match else 0.0
    commission_rm = _money_to_float(earn_match.group()) if earn_match else 0.0
    if price_match and earn_match and price_rm == commission_rm:
        # Same number ended up matching both fields - this happens when
        # OCR drops one of the two real values and leaves the "Earn"
        # label sitting next to the OTHER value instead. Don't fabricate
        # a duplicate reading; report no commission rather than a wrong one.
        commission_rm = 0.0

    return {
        "title": title.text,
        "price_rm": price_rm,
        "commission_rm": commission_rm,
        "units_sold": _shorthand_to_int(sold_match.group(1)) if sold_match else 0,
        "review_score": float(rating_match.group(1)) if rating_match else 0.0,
        # FR-1.4's spirit: never lose the raw read, even though it's OCR text not JSON.
        "raw_ocr_text": " | ".join(line.text for line in lines),
    }


def _fix_money_ocr_errors(text: str) -> str:
    """Tesseract sometimes reads a digit as a similar-looking letter
    inside a money amount ('RM0.47' -> 'RMO.47'). That breaks
    PRICE_RE/EARN_RE, which then makes the line look like a fresh
    product title instead of price data. Only fix digits INSIDE 'RM...'
    tokens so real title text is never touched."""
    return _MONEY_TOKEN_RE.sub(lambda m: m.group().translate(_OCR_DIGIT_FIXES), text)


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


def get_image_height(png_bytes: bytes) -> int:
    """Used by categories.py to work out the tab-bar region as a
    fraction of screen height, rather than a hardcoded pixel value
    that would only be correct for one specific device resolution."""
    return Image.open(io.BytesIO(png_bytes)).height


def to_scraped_product_shape(p: dict) -> dict:
    """Converts an OCR'd card (flat 'Earn RMx.xx' commission) into the
    same dict shape scraper/filters.py and app/models.py expect
    (commission as a %, plus an explicit est_commission_rm). Shared by
    scrape.py and scrape_interactive.py so this conversion only lives
    in one place."""
    price = p["price_rm"]
    commission_rm = p["commission_rm"]
    return {
        "title": p["title"],
        "price_rm": price,
        "commission_percentage": round((commission_rm / price) * 100, 2) if price else 0.0,
        "est_commission_rm": commission_rm,
        "review_score": p["review_score"],
        "stock_volume": 0,  # not shown on any OCR'd screen we've found so far
        "units_sold": p["units_sold"],
        "product_url": "",  # OCR has no URL to offer
        "raw_payload": p["raw_ocr_text"],  # FR-1.4 spirit: keep the raw read, even though it's OCR text not JSON
    }
