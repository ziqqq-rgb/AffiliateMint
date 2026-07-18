# backend/scraper/mobile/debug_cold_launch.py
"""
Captures exactly what the screen looks like right after a scripted
cold launch (terminate_app + activate_app), with NO manual navigation
in between - this is what scrape.py actually sees before its first
tap, which can differ from what you see browsing by hand.

Usage:
    cd backend
    python -m scraper.mobile.debug_cold_launch
"""

from scraper.mobile.driver import app_session
from scraper.mobile.ocr import screenshot_to_lines

SCREENSHOT_PATH = "debug_cold_launch.png"


def main() -> None:
    with app_session() as driver:
        # app_session() already waits after activate_app - screenshot
        # immediately, no extra input() so this matches scrape.py exactly
        png_bytes = driver.get_screenshot_as_png()

    with open(SCREENSHOT_PATH, "wb") as f:
        f.write(png_bytes)
    print(f"Saved cold-launch screenshot to {SCREENSHOT_PATH} - open it now.\n")

    lines = screenshot_to_lines(png_bytes)
    print(f"Text found on screen ({len(lines)} lines):")
    for line in lines:
        print(f"  top={line.top:4d}  {line.text!r}")


if __name__ == "__main__":
    main()