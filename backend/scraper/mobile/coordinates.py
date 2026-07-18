"""
Tap coordinates for the fixed navigation path through TikTok's app -
home screen -> Profile -> Shop tab -> Creator Centre -> Products ->
Product ranking (mapped from screenshots on 18 Jul 2026).

Coordinates are stored as FRACTIONS of screen width/height (0.0-1.0),
NOT raw pixels. The screenshots used to map these were taken on a
mirrored display at a different resolution than the phone Appium
actually drives. navigate.py converts these fractions to real pixels
using the connected device's own screen size at runtime, so this file
doesn't need to change if the device or resolution changes.

If TikTok ships a new layout and a tap lands wrong, this is the ONLY
file that should need updating (same isolation principle as
scraper/config.py - NFR 5.5).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TapStep:
    name: str
    x_fraction: float
    y_fraction: float
    wait_seconds: float = 2.0
    # Text expected on screen AFTER this tap lands. Used to fail loudly
    # if the tap didn't do what we expected (NFR 5.1) instead of
    # silently continuing on the wrong screen.
    expect_text: Optional[str] = None


# Walked top to bottom, in order. Each step assumes the previous one
# landed correctly.
HOME_TO_PRODUCT_RANKING: list[TapStep] = [
    TapStep(
        name="open_profile",
        x_fraction=0.900,
        y_fraction=0.793,
        expect_text="Following",
    ),
    TapStep(
        name="open_shop_tab",
        x_fraction=0.256,
        y_fraction=0.393,
        expect_text="Creator Centre",
    ),
    TapStep(
        name="open_creator_centre",
        x_fraction=0.499,
        y_fraction=0.434,
        expect_text="Creator Centre",
    ),
    TapStep(
        name="open_products_tab",
        x_fraction=0.375,
        y_fraction=0.793,
        expect_text="Discover",
    ),
    TapStep(
        name="open_product_ranking",
        x_fraction=0.148,
        y_fraction=0.330,
        expect_text="Product ranking",
    ),
]