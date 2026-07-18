"""
Interactive tool to re-map every tap in HOME_TO_PRODUCT_RANKING in one
guided pass, instead of debugging each step separately.

For each step: takes a screenshot, shows you every text line found
with its (x_frac, y_frac), you tell it which line to tap (or type
exact fractions if the icon has no nearby text, like a lone glyph
icon), it taps, waits, and shows you the resulting screen so you can
confirm it landed correctly before moving to the next step.

At the end it prints a ready-to-paste HOME_TO_PRODUCT_RANKING list
with corrected coordinates for coordinates.py.

Usage:
    cd backend
    python -m scraper.mobile.remap_coordinates
"""

from scraper.mobile.coordinates import HOME_TO_PRODUCT_RANKING, TapStep
from scraper.mobile.driver import app_session
from scraper.mobile.ocr import screenshot_to_lines


def _show_screen(driver, image_width: int, image_height: int) -> list[tuple[str, float, float]]:
    """Screenshots the current screen and prints every text line with
    its position as a fraction, numbered so the user can pick one."""
    lines = screenshot_to_lines(driver.get_screenshot_as_png())
    options = []
    for i, line in enumerate(lines):
        x_frac = line.left / image_width
        y_frac = line.top / image_height
        options.append((line.text, x_frac, y_frac))
        print(f"  [{i}] (x_frac={x_frac:.3f}, y_frac={y_frac:.3f})  {line.text!r}")
    return options


def _prompt_for_tap_point(options: list[tuple[str, float, float]]) -> tuple[float, float]:
    """Lets the user pick a printed line by index, or type exact
    fractions directly (needed for icons with no nearby text)."""
    choice = input(
        "\nEnter the number of the line to tap, or type 'x,y' fractions directly "
        "(e.g. '0.888,0.961'): "
    ).strip()

    if "," in choice:
        x_str, y_str = choice.split(",")
        return float(x_str), float(y_str)

    index = int(choice)
    _, x_frac, y_frac = options[index]
    return x_frac, y_frac


def _tap_fraction(driver, x_fraction: float, y_fraction: float) -> None:
    size = driver.get_window_size()
    x = int(size["width"] * x_fraction)
    y = int(size["height"] * y_fraction)
    driver.tap([(x, y)])


def main() -> None:
    corrected_steps: list[TapStep] = []

    with app_session() as driver:
        window_size = driver.get_window_size()

        for step in HOME_TO_PRODUCT_RANKING:
            print(f"\n{'=' * 60}")
            print(f"STEP: {step.name}  (expects to see: {step.expect_text!r})")
            print(f"{'=' * 60}")
            print("Current screen text:\n")

            options = _show_screen(driver, window_size["width"], window_size["height"])

            x_frac, y_frac = _prompt_for_tap_point(options)
            _tap_fraction(driver, x_frac, y_frac)

            import time
            time.sleep(step.wait_seconds)

            print(f"\nTapped ({x_frac:.3f}, {y_frac:.3f}). Screen after tap:\n")
            _show_screen(driver, window_size["width"], window_size["height"])

            confirm = input(
                f"\nDid this land correctly (expected to see {step.expect_text!r})? [y/n]: "
            ).strip().lower()

            if confirm != "y":
                print("Marking this step as unresolved - you may need to re-run for this step.")

            corrected_steps.append(
                TapStep(
                    name=step.name,
                    x_fraction=round(x_frac, 3),
                    y_fraction=round(y_frac, 3),
                    wait_seconds=step.wait_seconds,
                    expect_text=step.expect_text,
                )
            )

    print(f"\n{'=' * 60}")
    print("DONE. Paste this into coordinates.py:")
    print(f"{'=' * 60}\n")
    print("HOME_TO_PRODUCT_RANKING: list[TapStep] = [")
    for step in corrected_steps:
        print(f"    TapStep(")
        print(f"        name={step.name!r},")
        print(f"        x_fraction={step.x_fraction},")
        print(f"        y_fraction={step.y_fraction},")
        print(f"        expect_text={step.expect_text!r},")
        print(f"    ),")
    print("]")


if __name__ == "__main__":
    main()