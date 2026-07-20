"""
backend/scraper/run.py
HYBRID STEALTH SCRAPER (Fixed CAPTCHA Detector + Dual DOM & Wiretap Harvester)
"""
import os
import time
import json
from seleniumbase import Driver
from playwright.sync_api import sync_playwright


def run_hybrid_scraper(target_url: str):
    print("--- Starting Fixed Hybrid Stealth Scraper ---")
    
    # 1. SELENIUMBASE DEFENSE: Launch UC Mode
    print("[+] Launching SeleniumBase UC Mode to bypass anti-bot defenses...")
    driver = Driver(uc=True, incognito=True, headless=False)
    
    harvested_items = []
    seen_titles = set()

    def add_product(title: str, price: str, url: str = "", img: str = "", source: str = "DOM"):
        if not title or title in seen_titles or len(title.strip()) < 3:
            return
        clean_title = title.strip()
        seen_titles.add(clean_title)
        item = {
            "title": clean_title,
            "price_rm": price,
            "product_url": url,
            "image_url": img,
            "source": source
        }
        harvested_items.append(item)
        print(f"  [{source} HARVEST #{len(harvested_items)}] -> {clean_title[:45]}... | RM {price}")

    try:
        print(f"[+] Navigating to target -> {target_url}")
        driver.get(target_url)
        time.sleep(3)

        # =================================================================
        # FIX 1: SMART VISIBLE CAPTCHA DETECTOR (No more false positives!)
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

            # --- WIRETAP HANDLER ---
            def handle_response(response):
                url = response.url.lower()
                if any(kw in url for kw in ["/oec/", "showcase", "goods", "commodity", "search", "card_list", "product", "homepage_deskt", "/api/"]):
                    try:
                        if "json" in response.headers.get("content-type", ""):
                            data = response.json()
                            parse_json_recursive(data)
                    except Exception:
                        pass

            def parse_json_recursive(obj):
                if isinstance(obj, dict):
                    has_price = any(k in obj for k in ["product_price_info", "price", "sale_price", "price_info", "sale_price_decimal"])
                    has_title = any(k in obj for k in ["title", "product_name", "name"]) and len(str(obj.get("title", ""))) > 5
                    if has_price and has_title:
                        title = obj.get("title") or obj.get("product_name") or obj.get("name")
                        price = "0.00"
                        if isinstance(obj.get("product_price_info"), dict):
                            price = obj["product_price_info"].get("sale_price_decimal") or obj["product_price_info"].get("origin_price_decimal", "0.00")
                        elif obj.get("sale_price"):
                            price = str(obj.get("sale_price"))
                        elif obj.get("price"):
                            price = str(obj.get("price"))
                        add_product(title, price, source="WIRETAP")
                    else:
                        for v in obj.values():
                            parse_json_recursive(v)
                elif isinstance(obj, list):
                    for item in obj:
                        parse_json_recursive(item)

            page.on("response", handle_response)
            print("[+] Playwright network wiretap ACTIVE!")

            # --- DOM SCRAPER HELPER ---
            def scrape_visible_dom_products():
                return page.evaluate("""
                    (() => {
                        const items = [];
                        // Select candidate elements containing price/product data
                        const candidates = document.querySelectorAll('a, div[class*="Card"], div[class*="product"], div[class*="Item"], div[class*="goods"]');
                        
                        candidates.forEach(el => {
                            const text = el.textContent || "";
                            if (text.includes("RM") && (text.includes("sold") || text.includes("%") || text.includes("Arrivals") || text.includes("Kelabu"))) {
                                const priceMatch = text.match(/RM\\s*([0-9\\.,]+)/);
                                
                                // Find title text inside element
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
                                        price: priceMatch[1],
                                        url: linkEl ? linkEl.href : "",
                                        img: imgEl ? imgEl.src : ""
                                    });
                                }
                            }
                        });
                        return items;
                    })();
                """)

            # HARVEST 1: Scrape rendered items on load
            print("[+] Harvesting products visible on initial screen...")
            for p_item in scrape_visible_dom_products():
                add_product(p_item["title"], p_item["price"], p_item["url"], p_item["img"], source="DOM")

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
                
                # Scrape newly rendered DOM elements after each scroll
                for p_item in scrape_visible_dom_products():
                    add_product(p_item["title"], p_item["price"], p_item["url"], p_item["img"], source="DOM")

            pw_browser.close()

    except Exception as e:
        print(f"\n[ERROR] Hybrid execution failed: {e}")
        
    finally:
        print("\n[+] Closing SeleniumBase defense browser...")
        driver.quit()
        
        print("\n--- Final Scrape Summary ---")
        if len(harvested_items) > 0:
            print(f"[SUCCESS] Total products extracted: {len(harvested_items)}")
            output_file = "tiktok_harvest.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(harvested_items, f, indent=2, ensure_ascii=False)
            print(f"[SUCCESS] Saved entire catalog to {os.path.abspath(output_file)}!")
        else:
            print("[!] No products harvested.")
        print("--- Scrape Complete ---")


if __name__ == "__main__":
    run_hybrid_scraper("https://shop.tiktok.com/my")