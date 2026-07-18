"""
Autonomous navigation through the TikTok app - replaces the manual
"press Enter once you're on the right screen" step in scrape.py
(design doc FR-1.5: on-demand "run now" trigger, no operator needed).

Two tapping strategies, matching two different parts of the UI:
  - FIXED steps (open profile, open shop tab, ...) use hardcoded
    fractional coordinates from coordinates.py, because that part of
    the UI is the same every run.
  - CATEGORY and PRODUCT selection use OCR to find the requested text
    on screen and tap its center, because those lists are dynamic and
    scrollable - a fixed coordinate would only work by luck.
"""

import logging
import time

from appium.webdriver.webdriver import WebDriver

from scraper.mobile.coordinates import HOME_TO_PRODUCT_RANKING
from scraper.mobile.ocr import OcrLine, screenshot_to_lines

logger = logging.getLogger(__name__)


class NavigationError(RuntimeError):
    """A tap didn't land on the screen we expected. Raised instead of
    silently continuing (NFR 5.1: fail loudly, not silently)."""


def navigate_to_product_ranking(driver: WebDriver) -> None:
    """Walks the fixed tap path from app-open to the Product ranking
    screen. Raises NavigationError the moment a step doesn't land
    where expected, rather than blindly continuing."""
    for step in HOME_TO_PRODUCT_RANKING:
        _tap_fraction(driver, step.x_fraction, step.y_fraction)
        time.sleep(step.wait_seconds)

        if step.expect_text and not _screen_shows(driver, step.expect_text):
            raise NavigationError(
                f"After '{step.name}', expected to see {step.expect_text!r} "
                f"on screen but didn't. TikTok's layout may have changed - "
                f"re-map coordinates.py using scraper/mobile/debug_ocr.py."
            )

    logger.info("Reached Product ranking screen.")


def open_product_type_list(driver: WebDriver, product_type: str) -> None:
    """From the Product ranking screen, drills into the full list for
    one product type (e.g. "Tea") - the screen scrape_products() reads
    from.

    Tapping the "Tea" heading itself isn't the actual link - each
    section has a small "N new products >" line next to its heading,
    and THAT'S what opens the full list. This matters because the
    ranking overview only shows commission, not selling price, so it
    isn't enough data on its own (no way to compute
    commission_percentage without a price) - the full list is the
    real scrape target.
    """
    lines = screenshot_to_lines(driver.get_screenshot_as_png())
    heading = next((line for line in lines if line.text.strip().lower() == product_type.lower()), None)
    if heading is None:
        raise NavigationError(
            f"No section heading matching {product_type!r} found on the "
            f"Product ranking screen."
        )

    # The "N new products >" link sits in the same header row as the
    # heading, not below it. Look for it there; if OCR didn't catch it
    # (e.g. low confidence), fall back to tapping the heading itself.
    same_row = [line for line in lines if abs(line.top - heading.top) <= 20]
    link = next((line for line in same_row if "new product" in line.text.lower()), None)
    target = link or heading

    driver.tap([(target.left, target.top)])
    time.sleep(2.0)


def open_first_product(driver: WebDriver) -> None:
    """Taps the first product title on the current list screen to open
    its detail page. Optional - not used by the default scrape run,
    which reads prices/commission straight off the list screen."""
    lines = screenshot_to_lines(driver.get_screenshot_as_png())
    title = _guess_title_line(lines)
    if title is None:
        raise NavigationError("No product title found on screen to tap.")
    driver.tap([(title.left, title.top)])


def _guess_title_line(lines: list[OcrLine]) -> OcrLine | None:
    """Same heuristic scraper/mobile/ocr.py already uses for titles:
    longest line that isn't a price/sold-count line."""
    candidates = [
        line
        for line in lines
        if len(line.text) > 8 and "RM" not in line.text and "sold" not in line.text.lower()
    ]
    return max(candidates, key=lambda line: len(line.text)) if candidates else None


def _tap_fraction(driver: WebDriver, x_fraction: float, y_fraction: float) -> None:
    size = driver.get_window_size()
    x = int(size["width"] * x_fraction)
    y = int(size["height"] * y_fraction)
    driver.tap([(x, y)])


def _screen_shows(driver: WebDriver, text: str) -> bool:
    lines = screenshot_to_lines(driver.get_screenshot_as_png())
    return any(text.lower() in line.text.lower() for line in lines)


def _tap_matching_text(driver: WebDriver, text: str) -> None:
    lines = screenshot_to_lines(driver.get_screenshot_as_png())
    match = next((line for line in lines if text.lower() in line.text.lower()), None)
    if match is None:
        raise NavigationError(f"Could not find {text!r} anywhere on screen to tap.")
    driver.tap([(match.left, match.top)])