"""Clicks each shortlisted product's 'Get Link' button while its card is
still in the DOM, and reads the matching network response.

Matches buttons to offers POSITIONALLY (i-th offer in offers_on_page <->
i-th "Get Link" button in DOM order), instead of parsing an item id out
of the card's own product-page link. The DOM-extraction approach
(closest() + regex on an <a href>) proved unreliable across repeated
debugging - it likely returns null because these cards use client-side
routing rather than a plain <a href="/product/..."> anchor. Since
offers_on_page is built straight from the JSON API response (which
preserves array order) and the grid renders that same list top-to-
bottom, positional pairing is simpler and has actually been verified to
work, unlike the DOM-scraping approach.
"""
import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from scraper.pacing import human_pause
from scraper.shopee.config import config

logger = logging.getLogger(__name__)

GET_LINK_BUTTON_SELECTOR = "button.AffiliateItemCard__getlinkBtn"
GET_LINK_RESPONSE_URL_HINT = "productOfferLinks"

MODAL_CLOSE_SELECTOR = (
    '[class*="modal" i] [class*="close" i], '
    '[aria-label="Close" i], '
    '[class*="Modal__close" i]'
)


def _close_link_modal(page: Page, timeout_ms: int = 3000) -> None:
    """Closes the 'Get Link' popup so the next button isn't blocked.
    We already read the link from the network response, so we don't
    need to click 'Copy' - just get the popup out of the way."""
    close_btn = page.locator(MODAL_CLOSE_SELECTOR).first
    try:
        close_btn.wait_for(state="visible", timeout=timeout_ms)
        close_btn.click()
        return
    except PlaywrightTimeoutError:
        pass

    # Fallback: Escape key closes most modal implementations even
    # without a matched close button.
    try:
        page.keyboard.press("Escape")
    except Exception as e:
        logger.warning(f"[!] Could not close Get Link popup: {e}")


def fetch_links_for_page(page: Page, offers_on_page: list[dict], timeout_ms: int = 10000) -> None:
    """Mutates each dict in offers_on_page, setting affiliate_link in
    place, by clicking buttons in the same order the offers were
    parsed. Best-effort per item - a failed click/capture just leaves
    that one item's link empty rather than aborting the page."""
    buttons = page.locator(GET_LINK_BUTTON_SELECTOR)
    count = buttons.count()
    logger.info(f"[+] {count} 'Get Link' buttons on screen for {len(offers_on_page)} offers to fetch")

    if count != len(offers_on_page):
        logger.warning(
            f"[!] Button count ({count}) != offer count ({len(offers_on_page)}) - "
            "positional matching may misalign, proceeding on the shorter length"
        )

    pair_count = min(count, len(offers_on_page))
    for i in range(pair_count):
        offer = offers_on_page[i]
        item_id = str(offer["shopee_item_id"])
        button = buttons.nth(i)
        button.scroll_into_view_if_needed()

        try:
            with page.expect_response(
                lambda r: GET_LINK_RESPONSE_URL_HINT in r.url, timeout=timeout_ms
            ) as response_info:
                button.click()
            body = response_info.value.json()
            links = body.get("data", {}).get("productOfferLinks", [])
            match = next((l for l in links if str(l.get("itemId")) == item_id), None)
            offer["affiliate_link"] = match.get("productOfferLink", "") if match else ""
            if not match:
                logger.warning(f"[!] Button #{i} response didn't contain expected itemId {item_id}")
        except PlaywrightTimeoutError:
            logger.warning(f"[!] No response within {timeout_ms}ms for item {item_id} (button #{i})")
            offer["affiliate_link"] = ""
        except Exception as e:
            logger.warning(f"[!] Get Link failed for item {item_id} (button #{i}): {e}")
            offer["affiliate_link"] = ""
        finally:
            _close_link_modal(page)
            human_pause(config.min_delay_seconds, config.max_delay_seconds)