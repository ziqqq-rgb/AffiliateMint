"""
backend/scraper/dom_scraper.py

DOM-based fallback product scraping for scraper/run.py, used alongside
the network wiretap (wiretap.py) since not every rendered product
triggers a fresh API call (e.g. items already present in the initial
page load never fire a wiretap-visible request).
"""
from playwright.sync_api import Page

SCRAPE_VISIBLE_PRODUCTS_JS = """
(() => {
    const items = [];
    const candidates = document.querySelectorAll('a, div[class*="Card"], div[class*="product"], div[class*="Item"], div[class*="goods"]');

    candidates.forEach(el => {
        const text = el.textContent || "";
        if (text.includes("RM") && (text.includes("sold") || text.includes("%") || text.includes("Arrivals") || text.includes("Kelabu"))) {
            const priceMatch = text.match(/RM\\s*([0-9\\.,]+)/);

            let title = "";
            const heading = el.querySelector('h3, h4, span[class*="title"], div[class*="title"], p');
            if (heading) {
                title = heading.textContent.trim();
            } else {
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 10 && !l.includes('RM') && !l.includes('sold'));
                if (lines.length > 0) title = lines[0];
            }

            const imgEl = el.querySelector('img');
            const linkEl = el.tagName === 'A' ? el : el.querySelector('a');

            if (title && priceMatch) {
                items.push({
                    title: title,
                    sale_price_rm: priceMatch[1],
                    product_url: linkEl ? linkEl.href : "",
                    image_url: imgEl ? imgEl.src : "",
                    original_price_rm: "0.00",
                    discount_percentage: "",
                    savings_amount: "",
                    units_sold: 0,
                    rating_score: 0.0,
                    review_count: 0,
                    shop_name: "DOM Extracted",
                    shop_id: "",
                    free_shipping: false
                });
            }
        }
    });
    return items;
})();
"""


def scrape_visible_dom_products(page: Page) -> list[dict]:
    """Reads whatever product-like cards are currently rendered on
    screen - the fallback for items the network wiretap never saw a
    fresh API call for."""
    return page.evaluate(SCRAPE_VISIBLE_PRODUCTS_JS)
