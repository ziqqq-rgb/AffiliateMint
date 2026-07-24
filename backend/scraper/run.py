"""
backend/scraper/run.py
ADVANCED HYBRID AFFILIATE INTELLIGENCE ENGINE
Extracts 14+ deep affiliate metrics per product (Sales Volume, Discounts, Ratings, Shop Data)
"""
import os
import time
import json
from seleniumbase import Driver
from playwright.sync_api import sync_playwright
from scraper.browser import StealthBrowser
from scraper.capture_session import SessionManager
from scraper.session_store import load_cookies



def run_hybrid_scraper(target_url, category=None, min_rating=None, sort_by_sold=False, min_price=None, max_price=None):
    print("--- Starting Advanced Hybrid Affiliate Scraper ---")
    print("[+] Launching SeleniumBase UC Mode to bypass anti-bot defenses...")
    driver = Driver(uc=True, incognito=False, headless=False)

    harvested_items = []
    seen_ids_or_titles = set()


    def add_product(item_data: dict, source: str = "WIRETAP"):
        # Use product_id as primary deduplication key, fallback to title
        unique_key = item_data.get("product_id") or item_data.get("title")
        if not unique_key or unique_key in seen_ids_or_titles or len(str(item_data.get("title", "")).strip()) < 3:
            return
            
        seen_ids_or_titles.add(unique_key)
        item_data["source"] = source
        harvested_items.append(item_data)
        
        # Live Stream Terminal Display
        title_short = str(item_data.get("title", ""))[:40]
        price = item_data.get("sale_price_rm", "0.00")
        sold = item_data.get("units_sold", "N/A")
        discount = item_data.get("discount_percentage", "")
        disc_str = f" ({discount} OFF)" if discount else ""
        
        print(f"  [{source} #{len(harvested_items)}] -> {title_short}... | RM {price}{disc_str} | Sold: {sold}")

    try:
        print(f"[+] Loading session + navigating to target -> {target_url}")
        load_cookies(driver, target_url, "affiliate_session.txt")
        time.sleep(3.5)

        # =================================================================
        # SMART VISIBLE CAPTCHA DETECTOR
        # =================================================================
        print("[+] Checking for active visible CAPTCHA...")
        is_captcha_visible = driver.execute_script("""
            (() => {
                const modal = document.querySelector('#secsdk-captcha-drag-wrapper, .captcha_verify_container, [id*="captcha-drag"]');
                if (modal && modal.offsetWidth > 0 && modal.offsetHeight > 0) return true;
                const bodyText = document.body ? document.body.textContent : "";
                return bodyText.includes("Verify to continue") || bodyText.includes("Slide to verify");
            })();
        """)

        if is_captcha_visible:
            print("  [!] Active CAPTCHA detected on screen! Waiting 15s for manual solve...")
            time.sleep(15)
        else:
            print("  [SUCCESS] No active CAPTCHA blocking screen!")

        # 2. CONNECT PLAYWRIGHT OVER CDP
        debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        print(f"[+] Connecting Playwright to CDP Endpoint: http://{debugger_address}")

        with sync_playwright() as p:
            pw_browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
            context = pw_browser.contexts[0]
            page = context.pages[0]

            # --- DEEP JSON WIRETAP EXTRACTOR ---
            def extract_rich_product_data(obj: dict) -> dict:
                """Maps out all rich affiliate fields from TikTok's backend API payload."""
                price_info = obj.get("product_price_info", {})
                rate_info = obj.get("rate_info", {})
                sold_info = obj.get("sold_info", {})
                seller_info = obj.get("seller_info", {})
                seo_url = obj.get("seo_url", {})
                image_data = obj.get("image", {})
                marketing_info = obj.get("product_marketing_info", {})
                
                # Image URL extraction
                url_list = image_data.get("url_list", [])
                image_url = url_list[0] if url_list else ""
                
                # Check Free Shipping status
                free_shipping = False
                labels = marketing_info.get("placement_labels", {})
                for group in labels.values():
                    if isinstance(group, list):
                        for label in group:
                            if "free shipping" in str(label.get("text", "")).lower() or label.get("da_info", "").find("free_shipping") != -1:
                                free_shipping = True
                                break

                return {
                    "product_id": str(obj.get("product_id", "")),
                    "title": str(obj.get("title") or obj.get("product_name") or "").strip(),
                    "sale_price_rm": str(price_info.get("sale_price_decimal") or price_info.get("sale_price") or "0.00"),
                    "original_price_rm": str(price_info.get("origin_price_decimal") or price_info.get("origin_price") or "0.00"),
                    "discount_percentage": str(price_info.get("discount_format", "")),
                    "savings_amount": str(price_info.get("reduce_price_format", "")),
                    "units_sold": int(sold_info.get("sold_count", 0)) if sold_info.get("sold_count") else 0,
                    "rating_score": float(rate_info.get("score", 0.0)) if rate_info.get("score") else 0.0,
                    "review_count": int(rate_info.get("review_count", 0)) if str(rate_info.get("review_count", "0")).isdigit() else 0,
                    "shop_name": str(seller_info.get("shop_name", "")),
                    "shop_id": str(seller_info.get("seller_id", "")),
                    "free_shipping": free_shipping,
                    "product_url": str(seo_url.get("canonical_url", "")),
                    "image_url": image_url
                }

            def parse_json_recursive(obj):
                if isinstance(obj, dict):
                    has_price = any(k in obj for k in ["product_price_info", "price", "sale_price", "price_info", "sale_price_decimal"])
                    has_title = any(k in obj for k in ["title", "product_name", "name"]) and len(str(obj.get("title", ""))) > 5
                    
                    if has_price and has_title:
                        rich_data = extract_rich_product_data(obj)
                        if rich_data["title"] and float(rich_data["sale_price_rm"]) > 0:
                            add_product(rich_data, source="WIRETAP")
                    else:
                        for v in obj.values():
                            parse_json_recursive(v)
                elif isinstance(obj, list):
                    for item in obj:
                        parse_json_recursive(item)

            def handle_response(response):
                url = response.url.lower()
                if any(kw in url for kw in ["/oec/", "showcase", "goods", "commodity", "search", "card_list", "product", "homepage_deskt", "/api/"]):
                    try:
                        if "json" in response.headers.get("content-type", ""):
                            data = response.json()
                            parse_json_recursive(data)
                    except Exception:
                        pass

            page.on("response", handle_response)
            print("[+] Deep JSON Wiretap Extractor ACTIVE!")

            # --- DOM SCRAPER FALLBACK ---
            def scrape_visible_dom_products():
                return page.evaluate("""
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
                """)

            # HARVEST 1: Scrape rendered items on load
            print("[+] Harvesting initial screen products...")
            for p_item in scrape_visible_dom_products():
                add_product(p_item, source="DOM")

            # --- CLICK 'VIEW MORE' ---
            print("[+] Attempting to click 'View More' button...")
            try:
                view_more = page.locator('text=/View more/i').first
                if view_more.is_visible():
                    view_more.scroll_into_view_if_needed()
                    page.wait_for_timeout(1000)
                    view_more.click(force=True)
                    print("[SUCCESS] Clicked 'View More' button!")
                    page.wait_for_timeout(2500)
                else:
                    print("[!] 'View More' button not visible directly. Triggering scroll...")
            except Exception as e:
                print(f"[!] Could not click 'View More': {e}")

            # --- INFINITE SCROLL & CONTINUOUS HARVEST ---
            print("[+] Starting smooth mouse-wheel infinite scroll sequence...")
            for pass_num in range(1, 6):
                print(f"  -> Scroll pass {pass_num}/5...")
                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(2000)
                
                for p_item in scrape_visible_dom_products():
                    add_product(p_item, source="DOM")

            pw_browser.close()

    except Exception as e:
        print(f"\n[ERROR] Hybrid execution failed: {e}")
        
    finally:
        print("\n[+] Closing SeleniumBase defense browser...")
        driver.quit()
        
        print("\n--- Final Scrape Summary ---")
        if len(harvested_items) > 0:
            print(f"[SUCCESS] Total rich products extracted: {len(harvested_items)}")
            output_file = "tiktok_harvest.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(harvested_items, f, indent=2, ensure_ascii=False)
            print(f"[SUCCESS] Saved deep catalog to {os.path.abspath(output_file)}!")
        else:
            print("[!] No products harvested.")
        print("--- Scrape Complete ---")

    return harvested_items


if __name__ == "__main__":
    run_hybrid_scraper("https://shop.tiktok.com/my")