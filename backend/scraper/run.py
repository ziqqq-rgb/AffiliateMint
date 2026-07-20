"""
backend/scraper/run.py
Step 4: Main Execution Engine for AffiliateMint Scraper.
Orchestrates the StealthBrowser, SessionManager, and NetworkInterceptor into a unified pipeline.
"""
import os
import time
from backend.scraper.browser import StealthBrowser
from backend.scraper.capture_session import SessionManager
from backend.scraper.intercept import NetworkInterceptor

class AffiliateScraperEngine:
    def __init__(self, headless: bool = False, incognito: bool = True):
        """Initializes the core modules of our scraping stack."""
        self.browser = StealthBrowser(headless=headless, incognito=incognito)
        self.session_mgr = SessionManager(self.browser)
        self.interceptor = NetworkInterceptor(self.browser)
        self.is_running = False

    def start(self):
        """Launches the CDP browser and fires up the network wiretap."""
        if not self.is_running:
            self.browser.start()
            self.interceptor.start_intercepting()
            self.is_running = True

    def run_pipeline(
        self, 
        target_url: str, 
        domain_origin: str = None, 
        session_file: str = None, 
        filter_keywords: list = None
    ) -> dict:
        """
        Executes an end-to-end affiliate scraping job:
        1. Launches browser & starts background network wiretap.
        2. Loads cookies (if provided) to bypass authentication/login walls.
        3. Navigates to target URL and lets SPAs/dynamic data hydrate.
        4. Harvests visible metadata AND intercepted background JSON/API data.
        """
        try:
            self.start()

            # Step A: Configure wiretap keyword filters
            if filter_keywords:
                self.interceptor.set_filter_keywords(filter_keywords)
            else:
                # Default keywords relevant to affiliate tracking and campaign metrics
                self.interceptor.set_filter_keywords(["json", "api", "token", "campaign", "affiliate", "stats"])

            # Step B: Authenticate via saved session file (if provided and exists)
            if session_file and os.path.exists(session_file):
                if not domain_origin:
                    # Automatically extract the base domain URL (e.g., https://example.com)
                    domain_origin = "/".join(target_url.split("/")[:3])
                print(f"\n[+] Authenticating via saved session for origin: {domain_origin}")
                self.session_mgr.load_session(domain_url=domain_origin, filepath=session_file)
            elif session_file:
                print(f"\n[!] Notice: Session file '{session_file}' not found. Proceeding as unauthenticated guest...")

            # Step C: Clear old network logs and navigate to target campaign/dashboard
            self.interceptor.clear_log()
            print(f"\n[+] Executing target scrape -> {target_url}")
            self.browser.get(target_url)

            # Give initial SPA framework time to hydrate
            self.browser.driver.sleep(3.0)

            # =================================================================
            # NEW: Trigger Infinite Scroll to force background API payloads
            # =================================================================
            # Adjust max_scrolls depending on how many hundreds of products you want.
            # On TikTok Shop, each scroll pass typically fetches 20 to 30 products.
            self.browser.scroll_infinite(max_scrolls=12, base_pause=2.5)

            # Step D: Gather visible DOM metadata
            page_title = self.browser.driver.get_title()
            current_url = self.browser.driver.get_current_url()
            
            # Step E: Gather intercepted background network traffic
            network_data = self.interceptor.get_captured_data()

            # Structure the final data payload
            result_payload = {
                "success": True,
                "metadata": {
                    "title": page_title,
                    "url": current_url,
                    "timestamp": time.time()
                },
                "network_data": {
                    "total_requests": network_data["total_requests"],
                    "total_responses": network_data["total_responses"],
                    "captured_responses": network_data["responses"]
                }
            }

            print(f"[SUCCESS] Scrape completed cleanly for: '{page_title}'")
            return result_payload

        except Exception as e:
            print(f"\n[ERROR] Scraper pipeline encountered an error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        """Safely terminates all browser processes and cleans up."""
        if self.is_running:
            print("\n[+] Shutting down AffiliateScraper engine...")
            self.browser.stop()
            self.is_running = False

"""
backend/scraper/run.py
Main Execution Engine for AffiliateMint Scraper with SSR Extraction & Infinite Scroll.
"""
import os
import time
import json
from backend.scraper.browser import StealthBrowser
from backend.scraper.capture_session import SessionManager
from backend.scraper.intercept import NetworkInterceptor


# =====================================================================
# HELPER PARSERS & EXTRACTORS
# =====================================================================
def parse_tiktok_shop_item(item: dict) -> dict:
    """Maps raw TikTok product payload into clean ScrapedProduct schema."""
    price_info = item.get("product_price_info", {})
    rate_info = item.get("rate_info", {})
    sold_info = item.get("sold_info", {})
    seller_info = item.get("seller_info", {})
    seo_url = item.get("seo_url", {})
    image_data = item.get("image", {})
    
    url_list = image_data.get("url_list", [])
    first_image = url_list[0] if url_list else None

    return {
        "product_id": item.get("product_id"),
        "title": item.get("title"),
        "price_rm": float(price_info.get("sale_price_decimal", 0.0)) if price_info.get("sale_price_decimal") else 0.0,
        "original_price_rm": float(price_info.get("origin_price_decimal", 0.0)) if price_info.get("origin_price_decimal") else None,
        "review_score": float(rate_info.get("score", 0.0)) if rate_info.get("score") else None,
        "review_count": int(rate_info.get("review_count", 0)) if rate_info.get("review_count") else 0,
        "units_sold": sold_info.get("sold_count"),
        "shop_name": seller_info.get("shop_name"),
        "product_url": seo_url.get("canonical_url"),
        "image_url": first_image,
        "raw_payload": json.dumps(item)
    }


def extract_tiktok_ssr_catalog(driver) -> list:
    """Extracts initial SSR product catalog directly from script tags."""
    print("[+] Hunting across all script tags for SSR JSON payloads...")
    
    # Notice the 'r' right before the triple quotes below! This fixes the SyntaxWarning.
    js_query = r"""
    (() => {
        const scripts = document.querySelectorAll('script');
        const validPayloads = [];
        for (const s of scripts) {
            if (!s.textContent || s.textContent.length < 100) continue;
            try {
                validPayloads.push(JSON.parse(s.textContent));
            } catch (e) {
                const match = s.textContent.match(/(\{.*?\});?\s*$/s);
                if (match) {
                    try { validPayloads.push(JSON.parse(match[1])); } catch (err) {}
                }
            }
        }
        return validPayloads;
    })();
    """
    
    all_json_objects = driver.evaluate(js_query)
    if not all_json_objects:
        print("[!] No parsable JSON blobs found in script tags.")
        return []

    print(f"[+] Found {len(all_json_objects)} JSON blobs. Hunting for product items...")
    
    extracted_products = []
    
    def find_products_recursive(obj):
        if isinstance(obj, dict):
            # Target check: must contain product_id and price info
            if "product_id" in obj and "product_price_info" in obj:
                extracted_products.append(obj)
            else:
                for key, value in obj.items():
                    find_products_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                find_products_recursive(item)

    for blob in all_json_objects:
        find_products_recursive(blob)
        
    print(f"[SUCCESS] Harvested {len(extracted_products)} SSR products directly from HTML!")
    return extracted_products


# =====================================================================
# MAIN SCRAPER ENGINE
# =====================================================================
class AffiliateScraperEngine:
    def __init__(self, headless: bool = False, incognito: bool = True):
        self.browser = StealthBrowser(headless=headless, incognito=incognito)
        self.session_mgr = SessionManager(self.browser)
        self.interceptor = NetworkInterceptor(self.browser)
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.browser.start()
            self.interceptor.start_intercepting()
            self.is_running = True

    def run_pipeline(
        self, 
        target_url: str, 
        domain_origin: str = None, 
        session_file: str = None, 
        filter_keywords: list = None
    ) -> dict:
        try:
            self.start()

            # Step A: Configure wiretap keyword filters
            if filter_keywords:
                self.interceptor.set_filter_keywords(filter_keywords)
            else:
                self.interceptor.set_filter_keywords(["/oec/", "showcase", "goods", "commodity", "search", "card_list", "product", "/api/v1/shop/"])

            # Step B: Authenticate via saved session file (if provided)
            if session_file and os.path.exists(session_file):
                if not domain_origin:
                    domain_origin = "/".join(target_url.split("/")[:3])
                print(f"\n[+] Authenticating via saved session for origin: {domain_origin}")
                self.session_mgr.load_session(domain_url=domain_origin, filepath=session_file)

            # Step C: Clear logs and execute navigation + harvest
            self.interceptor.clear_log()
            print(f"\n[+] Executing target scrape -> {target_url}")
            
            # =================================================================
            # EXACT PLACEMENT: NAVIGATION + SSR HARVEST + INFINITE SCROLL
            # =================================================================
            self.browser.get(target_url)
            self.browser.driver.sleep(3.0)

            # PHASE 1: Harvest initial HTML SSR products from script tag
            ssr_raw_items = extract_tiktok_ssr_catalog(self.browser.driver)
            clean_ssr_products = [parse_tiktok_shop_item(item) for item in ssr_raw_items]
            
            print("\n--- Initial SSR Harvested Products ---")
            for p in clean_ssr_products:
                print(f"  [SSR] -> {p.get('title')[:45]}... | RM {p.get('price_rm')}")
            print("--------------------------------------\n")

            # =================================================================
            # NEW: DESTROY MODAL OVERLAYS & UNLOCK SCROLLING
            # =================================================================
            print("[+] Clearing potential login/cookie modal overlays...")
            unlock_js = """
            (() => {
                // Force body to allow scrolling if a modal locked it
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
                
                // Remove common backdrop overlays and cookie banners
                const selectors = [
                    '[class*="modal"]', '[class*="Dialog"]', '[class*="overlay"]', 
                    '[class*="cookie"]', '[class*="banner"]', '#secsdk-captcha-drag-wrapper'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el && el.style) el.style.display = 'none';
                    });
                });
            })();
            """
            self.browser.driver.evaluate(unlock_js)
            self.browser.driver.sleep(1.0)
            
            # PHASE 2: Trigger Infinite Scroll to catch background API traffic
            self.browser.scroll_infinite(max_scrolls=5, base_pause=2.5)
            # =================================================================

            # Step D: Gather metadata and intercepted API payloads
            page_title = self.browser.driver.get_title()
            current_url = self.browser.driver.get_current_url()
            network_data = self.interceptor.get_captured_data()

            return {
                "success": True,
                "metadata": {
                    "title": page_title,
                    "url": current_url,
                    "timestamp": time.time()
                },
                "ssr_products": clean_ssr_products,
                "network_data": {
                    "total_requests": network_data["total_requests"],
                    "total_responses": network_data["total_responses"],
                    "captured_responses": network_data["responses"]
                }
            }

        except Exception as e:
            print(f"\n[ERROR] Scraper pipeline encountered an error: {str(e)}")
            return {"success": False, "error": str(e)}

    def close(self):
        if self.is_running:
            print("\n[+] Shutting down AffiliateScraper engine...")
            self.browser.stop()
            self.is_running = False


# =====================================================================
# TEST RUNNER WITH PRODUCT PRINTER (SCOPE-SAFE)
# =====================================================================
if __name__ == "__main__":
    print("--- Starting TikTok Shop Infinite Scroll & Wiretap Harvest Test ---")
    
    engine = AffiliateScraperEngine(headless=False)
    target_shop_url = "https://shop.tiktok.com/my"
    
    try:
        results = engine.run_pipeline(target_url=target_shop_url)
        
        print("\n--- Final Test Summary ---")
        print(f"Status:        {'SUCCESS' if results.get('success') else 'FAILED'}")
        print(f"SSR Products:  {len(results.get('ssr_products', []))} items extracted directly from HTML!")
        print(f"API Calls:     {results['network_data']['total_responses']} matching API payloads intercepted!")
        
        # =================================================================
        # PRINTING ACTUAL PRODUCT TITLES & PRICES FROM WIRETAP PAYLOADS
        # =================================================================
        print("\n--- Intercepted Wiretap Products ---")
        
        # Using a list completely avoids Python global/nonlocal scope errors!
        harvested_items = []
        
        def hunt_and_print_items(obj):
            """Recursively searches intercepted JSON dictionaries for TikTok product items."""
            if isinstance(obj, dict):
                # Check if this dictionary represents a TikTok product
                if "product_id" in obj and "product_price_info" in obj:
                    title = obj.get("title", "Unknown Title")
                    price_dict = obj.get("product_price_info", {})
                    price = price_dict.get("sale_price_decimal", "0.00")
                    
                    harvested_items.append((title, price))
                    print(f"  [API Harvest #{len(harvested_items)}] -> {title[:50]}... | RM {price}")
                else:
                    for key, value in obj.items():
                        hunt_and_print_items(value)
            elif isinstance(obj, list):
                for item in obj:
                    hunt_and_print_items(item)

        # Loop through every background API call our wiretap caught
        for res in results["network_data"]["captured_responses"]:
            payload = res.get("payload")
            if payload:
                hunt_and_print_items(payload)
                
        if len(harvested_items) == 0:
            print("  [!] No product items found inside the intercepted API calls.")
        else:
            print(f"\n[SUCCESS] Extracted {len(harvested_items)} total products from background API wiretap!")
        print("------------------------------------\n")
        
    except Exception as e:
        print(f"\n[ERROR] Test Execution Failed: {e}")
        
    finally:
        engine.close()
        print("--- Test Complete ---")