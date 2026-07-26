"""Shopee affiliate scraper entry point - hybrid pattern like
scraper/run.py, but paginated (page 1, 2, 3...) rather than
infinite-scrolled - see pagination.py for why."""
import time

from playwright.sync_api import sync_playwright
from seleniumbase import Driver

from scraper.session_store import load_cookies, save_cookies
from scraper.shopee.auth import is_logged_in, wait_for_manual_login
from scraper.shopee.config import config
from scraper.shopee.filters import apply_filters
from scraper.shopee.intercept import parse_offer_response
from scraper.shopee.link_fetcher import fetch_links_for_page
from scraper.shopee.pagination import go_to_page, scroll_to_bottom
from scraper.pacing import human_pause


SESSION_FILE = "shopee_affiliate_session.txt"


def run_shopee_scraper(
    min_commission_rate: float | None = None,
    min_rating: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    driver = Driver(uc=True, incognito=False, headless=False)
    captured_offers: dict[str, dict] = {}

    try:
        load_cookies(driver, config.offer_page_url, SESSION_FILE)
        time.sleep(2.0)

        debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
            page = browser.contexts[0].pages[0]

            def handle_response(response):
                if config.offer_list_endpoint_hint not in response.url:
                    return
                try:
                    if "json" in response.headers.get("content-type", ""):
                        for offer in parse_offer_response(response.json()):
                            captured_offers[offer["shopee_item_id"]] = offer
                except Exception:
                    pass

            page.on("response", handle_response)
            page.goto(config.offer_page_url)
            page.wait_for_timeout(2500)

            if not is_logged_in(page):
                if not wait_for_manual_login(page):
                    raise RuntimeError("Shopee login timed out - no products scraped")
                save_cookies(driver, SESSION_FILE)
                page.goto(config.offer_page_url)
                page.wait_for_timeout(2500)

            # Resolve once here so the early-stop check during pagination
            # respects the SAME threshold the final filter will use.
            effective_min_commission = (
                min_commission_rate if min_commission_rate is not None else config.min_commission_rate
            )
            _harvest_pages(page, captured_offers, effective_min_commission)

            shortlist = apply_filters(
                list(captured_offers.values()),
                min_commission_rate=min_commission_rate,
                min_rating=min_rating,
                min_price=min_price,
                max_price=max_price,
            )
            browser.close()
            return shortlist
    finally:
        driver.quit()


def _harvest_pages(page, captured_offers: dict[str, dict], min_commission_rate: float) -> None:
    scroll_to_bottom(page)
    fetch_links_for_page(page, list(captured_offers.values()))  # page 1

    for page_num in range(2, config.max_pages + 1):
        if _enough_candidates(captured_offers, min_commission_rate):
            print(f"  -> Enough qualifying offers found, stopping early.")
            return

        print(f"  -> Harvesting page {page_num}/{config.max_pages} ({len(captured_offers)} offers so far)...")
        before_ids = set(captured_offers.keys())

        human_pause(config.min_delay_seconds, config.max_delay_seconds)
        if not go_to_page(page, page_num):
            print(f"  -> Page {page_num} not available - stopping.")
            return
        page.wait_for_timeout(2000)

        new_ids = set(captured_offers.keys()) - before_ids
        new_offers = [captured_offers[i] for i in new_ids]
        if new_offers:
            fetch_links_for_page(page, new_offers)


def _enough_candidates(offers: dict[str, dict], min_commission_rate: float) -> bool:
    passing = [o for o in offers.values() if o.get("commission_rate_pct", 0) >= min_commission_rate]
    return len(passing) >= config.shortlist_size