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

SESSION_FILE = "shopee_affiliate_session.txt"


def run_shopee_scraper(min_commission_rate: float | None = None) -> list[dict]:
    driver = Driver(uc=True, incognito=False, headless=False)

    # Keyed by shopee_item_id, NOT a plain list - the offer-list endpoint
    # can fire more than once for the same page (SPA re-renders, hover
    # prefetch, retries), which previously produced duplicate dict objects
    # for the same product. fetch_links_for_page would mutate one of the
    # duplicates while apply_filters' sort could return the OTHER,
    # unmutated one - links looked "successfully fetched" in logs but
    # never appeared in the final result. Keying by item id guarantees
    # exactly one dict object per product, so the mutation is always
    # visible in whatever gets returned.
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

            _harvest_pages(page, captured_offers)

            shortlist = apply_filters(list(captured_offers.values()))
            browser.close()
            return shortlist
    finally:
        driver.quit()


def _harvest_pages(page, captured_offers: dict[str, dict]) -> None:
    """Walks pages 1..max_pages, fetching that page's affiliate links
    immediately (buttons only exist while the page is rendered), and
    stopping early once enough qualifying offers are found."""
    scroll_to_bottom(page)
    fetch_links_for_page(page, list(captured_offers.values()))  # page 1

    for page_num in range(2, config.max_pages + 1):
        if _enough_candidates(captured_offers):
            print(f"  -> Enough qualifying offers found, stopping early.")
            return

        print(f"  -> Harvesting page {page_num}/{config.max_pages} ({len(captured_offers)} offers so far)...")
        before_ids = set(captured_offers.keys())

        if not go_to_page(page, page_num):
            print(f"  -> Page {page_num} not available - stopping.")
            return
        page.wait_for_timeout(2000)

        new_ids = set(captured_offers.keys()) - before_ids
        new_offers = [captured_offers[i] for i in new_ids]
        if new_offers:
            fetch_links_for_page(page, new_offers)


def _enough_candidates(offers: dict[str, dict]) -> bool:
    passing = [o for o in offers.values() if o.get("commission_rate_pct", 0) >= config.min_commission_rate]
    return len(passing) >= config.shortlist_size