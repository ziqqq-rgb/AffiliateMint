"""
Diagnostic tool for ai_extract.py - same idea as debug_ocr.py, but for
the NVIDIA vision path instead of Tesseract OCR.

Lets you point the phone at any product screen, take one screenshot,
and see exactly what the AI extracted - so you can sanity-check
outputs before trusting it inside scrape.py's full scroll loop.

Usage:
    cd backend
    python -m scraper.mobile.debug_ai_extract
"""

import json

from scraper.mobile.ai_extract import extract_products_with_ai
from scraper.mobile.driver import app_session, human_delay

SCREENSHOT_PATH = "debug_ai_screenshot.png"


def main() -> None:
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the product screen you want to debug.")
        input("Press Enter once it's on screen...\n")
        png_bytes = driver.get_screenshot_as_png()

    with open(SCREENSHOT_PATH, "wb") as f:
        f.write(png_bytes)
    print(f"Saved screenshot to {SCREENSHOT_PATH} - open it and confirm it's the right screen.\n")

    print("Sending to NVIDIA vision model...\n")
    try:
        products = extract_products_with_ai(png_bytes)
    except Exception as e:
        print(f"AI extraction failed: {e}")
        print("Check NVIDIA_API_KEY in .env and that the model name in config.py is valid.")
        return

    print(f"AI extracted {len(products)} product(s):\n")
    for p in products:
        print(json.dumps(p, indent=2))
        print()

    if not products:
        print("No products returned. Possible causes:")
        print("  - Screenshot doesn't actually show product cards (check the saved PNG)")
        print("  - Model refused/misunderstood the prompt (check raw response by adding a")
        print("    print(raw_text) inside ai_extract.py temporarily)")


if __name__ == "__main__":
    main()