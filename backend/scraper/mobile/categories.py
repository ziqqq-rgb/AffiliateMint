"""
Discovers tappable category labels on the Product Ranking screen so
navigate.py can drive TikTok without any fixed/guessed coordinates -
every tap target comes from OCR reading the CURRENT screen each run,
not a hardcoded pixel map that breaks the moment TikTok reflows a
layout.

Two things get discovered here, matching the two-step picker flow
(big category -> specific section):
  - discover_top_tabs: the horizontal tab row ("For you", "Food &
    Beverages", "Pet Supplies", ...) near the top of the screen.
    Built from raw WORD positions, not Tesseract's own line grouping -
    confirmed empirically that Tesseract merges an entire row of
    adjacent tab buttons into one single garbled "line", so tabs have
    to be reconstructed by clustering words on large horizontal gaps
    (~4-8px within one tab's own words vs ~30px+ between tabs).
  - discover_sub_categories: section headings inside the body (e.g.
    "Instant Hijab") identified by the "N new products >" link that
    sits in the same row - that link is what actually gets tapped.
    On the real screen this heading sits BELOW its anchor line, not
    above it - don't assume a direction, search both ways.
"""

import io
import re
from dataclasses import dataclass

import pytesseract
from PIL import Image
from pytesseract import Output

from scraper.mobile.ocr import MIN_CONFIDENCE, OcrLine

NEW_PRODUCTS_RE = re.compile(r"\d+\s*new products?", re.IGNORECASE)
_CLOCK_RE = re.compile(r"^\d{1,2}:\d{2}")

# Top ~16% of the screen covers the tab row on the devices we've
# tested (landscape tablet, 1280x800) - tune if tabs are being missed
# or body text is getting caught. Check with a debug print of
# `data["top"]` values for your device if this needs adjusting.
TAB_BAR_HEIGHT_FRACTION = 0.16

# Gap between two OCR'd WORDS bigger than this (in pixels) is treated
# as a boundary between two separate tabs, not two words in the same
# tab. Calibrated against a real screenshot: within-tab gaps were
# ~4-8px, between-tab gaps were ~30-35px - wide margin either side.
WORD_GAP_TAB_BOUNDARY_PX = 20

# Two words only belong to the same tab if they're also on the same
# visual row - without this, words from completely different rows
# (e.g. the status bar clock and the tab row below it) can end up in
# one cluster just because they're close in x-position once sorted.
ROW_TOLERANCE_PX = 15

# A heading counts as "belonging to" a "N new products" link if it
# sits within this many pixels of it on screen, ABOVE OR BELOW -
# TikTok's real layout puts the heading below the link, not above it.
HEADING_PROXIMITY_PX = 80


@dataclass
class TappableLabel:
    text: str
    tap_x: int
    tap_y: int


def discover_top_tabs(png_bytes: bytes) -> list[TappableLabel]:
    """Reads the horizontal category tab row by clustering individual
    OCR'd words by horizontal gap. Needs the raw screenshot (not
    pre-built OcrLines) because it works at the word level, not the
    line level - see the module docstring for why."""
    image = Image.open(io.BytesIO(png_bytes))
    band_height = image.height * TAB_BAR_HEIGHT_FRACTION
    data = pytesseract.image_to_data(image, output_type=Output.DICT)

    words = []
    for i, text in enumerate(data["text"]):
        if not text.strip() or int(data["conf"][i]) < MIN_CONFIDENCE:
            continue
        if data["top"][i] > band_height:
            continue
        words.append((text, data["left"][i], data["top"][i], data["width"][i]))

    labels = _cluster_words_by_gap(words)
    return [
        label
        for label in labels
        if not _CLOCK_RE.match(label.text)
        and "product ranking" not in label.text.lower()
    ]


def _cluster_words_by_gap(words: list[tuple]) -> list[TappableLabel]:
    if not words:
        return []
    words = sorted(words, key=lambda w: w[1])  # left to right

    clusters = [[words[0]]]
    for word in words[1:]:
        _, prev_left, prev_top, prev_width = clusters[-1][-1]
        gap = word[1] - (prev_left + prev_width)
        same_row = abs(word[2] - prev_top) <= ROW_TOLERANCE_PX
        if same_row and gap <= WORD_GAP_TAB_BOUNDARY_PX:
            clusters[-1].append(word)
        else:
            clusters.append([word])

    labels = []
    for cluster in clusters:
        text = " ".join(w[0] for w in cluster)
        left = min(w[1] for w in cluster)
        top = min(w[2] for w in cluster)
        right = max(w[1] + w[3] for w in cluster)
        labels.append(TappableLabel(text=text, tap_x=(left + right) // 2, tap_y=top + 15))
    return labels


def discover_sub_categories(lines: list[OcrLine]) -> list[TappableLabel]:
    """Finds section headings (e.g. "Instant Hijab") by looking for a
    short text line sitting near a "N new products" link - the same
    visual pattern a human uses to spot these sections. The link
    itself is what gets tapped (has a ">" affordance); the heading's
    text is what gets shown as the readable category name."""
    anchors = [l for l in lines if NEW_PRODUCTS_RE.search(l.text)]
    labels = []
    for anchor in anchors:
        heading = _nearest_heading(lines, anchor)
        if heading:
            labels.append(TappableLabel(text=heading.text, tap_x=anchor.left + 40, tap_y=anchor.top + 15))
    return labels


def _nearest_heading(lines: list[OcrLine], anchor: OcrLine) -> OcrLine | None:
    nearby = [
        l
        for l in lines
        if l is not anchor
        and abs(l.top - anchor.top) <= HEADING_PROXIMITY_PX
        and not NEW_PRODUCTS_RE.search(l.text)
        and "top selling" not in l.text.lower()
    ]
    return min(nearby, key=lambda l: abs(l.top - anchor.top)) if nearby else None
