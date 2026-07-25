"""Clicks each shortlisted product's 'Get Link' button while its card is
still in the DOM, and reads the matching network response
(data.productOfferLinks[0].productOfferLink).

Must run per-page, right after that page's offers are captured -
navigating to another page unmounts the current page's buttons, so
this can't be deferred until all pages are harvested (that was the
original bug: links always came back empty for anything past page 1).
"""
import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

GET_LINK_BUTTON_SELECTOR = "button.AffiliateItemCard__getlinkBtn"

_EXTRACT_ITEM_ID_JS = """
el => {
    const card = el.closest('[class*="ItemCard"]') || el.parentElement;
    const link = card ? card.querySelector('a[href*="/product/"]') : null;
    if (!link) return null;
    const match = link.href.match(/\\/product\\/\\d+\\/(\\d+)/);
    return match ? match[1] : null;
}
"""


def fetch_links_for_page(page: Page, offers_on_page: list[dict], timeout_ms: int = 8000) -> None:
    """Mutates each dict in offers_on_page, setting affiliate_link in
    place. Best-effort per item - a failed click/capture just leaves
    that one item's link empty rather than aborting the page."""
    wanted_ids = {str(o["shopee_item_id"]) for o in offers_on_page}
    by_item_id = {str(o["shopee_item_id"]): o for o in offers_on_page}

    buttons = page.locator(GET_LINK_BUTTON_SELECTOR)
    count = buttons.count()
    logger.info(f"[+] Found {count} 'Get Link' buttons on this page, {len(wanted_ids)} match the shortlist")

    for i in range(count):
        button = buttons.nth(i)
        item_id = button.evaluate(_EXTRACT_ITEM_ID_JS)
        if item_id not in wanted_ids:
            continue

        captured = {}

        def handle_response(response, item_id=item_id):  # default arg binds per-iteration value
            try:
                if "json" not in response.headers.get("content-type", ""):
                    return
                body = response.json()
                for link in body.get("data", {}).get("productOfferLinks", []):
                    if str(link.get("itemId")) == item_id:
                        captured["link"] = link.get("productOfferLink", "")
            except Exception:
                pass

        page.on("response", handle_response)
        try:
            button.scroll_into_view_if_needed()
            button.click(timeout=timeout_ms)
            page.wait_for_timeout(1500)
        except Exception as e:
            logger.warning(f"[!] Get Link click failed for item {item_id}: {e}")
        finally:
            page.remove_listener("response", handle_response)

        by_item_id[item_id]["affiliate_link"] = captured.get("link", "")