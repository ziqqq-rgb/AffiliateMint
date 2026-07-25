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

logger = logging.getLogger(__name__)

GET_LINK_BUTTON_SELECTOR = "button.AffiliateItemCard__getlinkBtn"
GET_LINK_RESPONSE_URL_HINT = "productOfferLinks"


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
            # Extra safety check: confirm the response actually names the
            # item we expected at this position, not just "a" response.
            match = next((l for l in links if str(l.get("itemId")) == item_id), None)
            if match:
                offer["affiliate_link"] = match.get("productOfferLink", "")
            else:
                logger.warning(f"[!] Button #{i} response didn't contain expected itemId {item_id}")
                offer["affiliate_link"] = ""
        except PlaywrightTimeoutError:
            logger.warning(f"[!] No response within {timeout_ms}ms for item {item_id} (button #{i})")
            offer["affiliate_link"] = ""
        except Exception as e:
            logger.warning(f"[!] Get Link failed for item {item_id} (button #{i}): {e}")
            offer["affiliate_link"] = ""