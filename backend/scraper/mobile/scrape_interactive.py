"""
Interactive entrypoint: discovers categories, asks once on Telegram,
scrapes the chosen one - all inside a SINGLE app session, so TikTok
is only launched once per run instead of restarting between steps.
"""

import logging

from scraper.mobile import navigate
from scraper.mobile.categories import discover_categories
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.scrape import scrape_current_screen
from scraper.mobile.telegram_notify import send_category_choices, wait_for_category_choice

logger = logging.getLogger(__name__)


def run() -> None:
    with app_session() as driver:
        human_delay()
        navigate.navigate_to_product_ranking(driver)

        categories, scroll_count = discover_categories(driver)
        if not categories:
            raise RuntimeError("No categories found on the Product ranking screen.")

        logger.info("Found %d categories - sending to Telegram.", len(categories))
        send_category_choices(categories)
        chosen = wait_for_category_choice(categories)
        logger.info("Operator chose %r.", chosen)

        # discovery scrolled to the bottom - walk back up before searching
        for _ in range(scroll_count):
            navigate.scroll_up(driver)
            human_delay()

        navigate.find_and_open_category(driver, chosen)
        results = scrape_current_screen(driver)

    print(f"Shortlisted {len(results)} products for {chosen!r}")
    for r in results:
        print(r)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()