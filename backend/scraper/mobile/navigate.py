"""
Autonomous navigation through the TikTok app - replaces the manual
"press Enter once you're on the right screen" step in scrape.py
(design doc FR-1.5: on-demand "run now" trigger, no operator needed).

Every tap target comes from OCR reading the CURRENT screen each time
(scraper/mobile/categories.py), never a hardcoded pixel map - that's
the only way this survives TikTok reflowing a layout at all.
"""

import time

from scraper.mobile.categories import TappableLabel


def tap_label(driver, label: TappableLabel) -> None:
    driver.tap([(label.tap_x, label.tap_y)])


def scroll_down(driver, screen_fraction: float = 0.6) -> None:
    """Swipes up to reveal more content below the fold."""
    size = driver.get_window_size()
    x = size["width"] // 2
    start_y = int(size["height"] * 0.75)
    end_y = int(size["height"] * (0.75 - screen_fraction))
    driver.swipe(x, start_y, x, end_y, duration=400)
    time.sleep(1.0)


def scroll_up(driver, screen_fraction: float = 0.6) -> None:
    """Reverse of scroll_down - used to walk back toward the top after
    discovery has scrolled all the way to the bottom."""
    size = driver.get_window_size()
    x = size["width"] // 2
    start_y = int(size["height"] * (0.75 - screen_fraction))
    end_y = int(size["height"] * 0.75)
    driver.swipe(x, start_y, x, end_y, duration=400)
    time.sleep(1.0)

def tap_xy(driver, x: int, y: int) -> None:
    """Taps raw pixel coordinates - used when the tap target came from
    the VLM agent (a plain {"x":.., "y":..} dict) rather than OCR's
    TappableLabel."""
    driver.tap([(x, y)])