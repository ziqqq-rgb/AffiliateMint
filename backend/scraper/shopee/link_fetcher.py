"""Clicks a shortlisted product's 'Get Link' button and reads the
matching network response (data.productOfferLinks[0].productOfferLink).
Kept separate from run.py so the harvest loop stays readable."""
import logging

from playwright.sync_api import Page

from scraper.shopee.config import config

logger = logging.getLogger(__name__)


def fetch_link_for_item(page: Page, item_id: str, timeout_ms: int = 8000) -> str:
    """Returns "" if the link never arrives — callers should skip that
    product rather than fail the whole scrape."""
    captured = {}

    def handle_response(response):
        if config.get_link_endpoint_hint not in response.url:
            return
        try:
            for link in response.json().get("data", {}).get("productOfferLinks", []):
                if str(link.get("itemId")) == str(item_id):
                    captured["link"] = link.get("productOfferLink", "")
        except Exception:
            pass

    page.on("response", handle_response)
    try:
        # TODO: confirm real selector via DevTools — this is a placeholder
        # matching how the UI's "Get Link" button is scoped per card.
        button = page.locator(f'[data-item-id="{item_id}"] >> text=Get Link').first
        button.click(timeout=timeout_ms)
        page.wait_for_timeout(2000)
    except Exception as e:
        logger.warning(f"[!] Get Link click failed for item {item_id}: {e}")
    finally:
        page.remove_listener("response", handle_response)

    return captured.get("link", "")