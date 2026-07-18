"""
Diagnostic tool for scrape.py - shows exactly what OCR reads off the
screen instead of just a final pass/fail count, so a "0 products"
result can actually be debugged instead of guessed at.

Saves the raw screenshot to disk (confirm it's really the screen you
think it is) and prints EVERY line Tesseract found, not just the ones
that matched a price/earn pattern - so you can see if OCR is reading
garbled text, reading nothing at all, or reading fine but the regex
just doesn't match your screen's exact wording.

Usage:
    cd backend
    python -m scraper.mobile.debug_ocr
"""

from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.ocr import extract_products, screenshot_to_lines

SCREENSHOT_PATH = "debug_screenshot.png"


def main() -> None:
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the product screen you want to debug.")
        input("Press Enter once it's on screen...\n")
        png_bytes = driver.get_screenshot_as_png()

    with open(SCREENSHOT_PATH, "wb") as f:
        f.write(png_bytes)
    print(f"Saved screenshot to {SCREENSHOT_PATH} - open it and confirm it's the right screen.\n")

    lines = screenshot_to_lines(png_bytes)
    print(f"Tesseract found {len(lines)} line(s) of text total:\n")
    if not lines:
        print("  (nothing at all - either the screenshot is blank/black, or")
        print("   Tesseract isn't installed correctly - run `tesseract --version`)")
    for line in lines:
        print(f"  top={line.top:4d}  {line.text!r}")

    products = extract_products(lines)
    print(f"\nOf those, {len(products)} matched a price/earn pattern and became a card:")
    for p in products:
        print(" ", p)

    if lines and not products:
        print("\nOCR is reading text fine, but none of it matched PRICE_RE or EARN_RE")
        print("in ocr.py. Look at the lines printed above - if a price/earn line IS")
        print("there but slightly different from 'RM14.88' or 'Earn RM2.73' (different")
        print("spacing, currency symbol, wording), send it to Claude to fix the regex.")


if __name__ == "__main__":
    main()
