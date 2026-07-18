# backend/scraper/mobile/debug_coordinates.py
import io

from PIL import Image

from scraper.mobile.driver import app_session
from scraper.mobile.ocr import screenshot_to_lines


def main() -> None:
    with app_session() as driver:
        png_bytes = driver.get_screenshot_as_png()

    image = Image.open(io.BytesIO(png_bytes))
    print(f"Screenshot size: {image.width} x {image.height}\n")

    lines = screenshot_to_lines(png_bytes)
    for line in lines:
        x_frac = line.left / image.width
        y_frac = line.top / image.height
        print(f"  (x_frac={x_frac:.3f}, y_frac={y_frac:.3f})  {line.text!r}")


if __name__ == "__main__":
    main()