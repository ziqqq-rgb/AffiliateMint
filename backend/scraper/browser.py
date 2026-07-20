import random
from seleniumbase import sb_cdp

class StealthBrowser:
    def __init__(self, headless: bool = False, incognito: bool = True):
        self.headless = headless
        self.incognito = incognito
        self.driver = None

    def start(self):
        print("[+] Launching stealth CDP browser...")
        self.driver = sb_cdp.Chrome(
            headless=self.headless,
            incognito=self.incognito,
            lang="en-US"
        )
        return self.driver

    def get(self, url: str):
        if not self.driver:
            self.start()
        print(f"[+] Navigating to: {url}")
        self.driver.goto(url)
        self.driver.sleep(2)

    def scroll_infinite(self, max_scrolls: int = 15, base_pause: float = 2.5):
        """
        Scrolls down incrementally to trigger lazy-loading and background JSON API requests.
        
        :param max_scrolls: Maximum number of scroll passes before stopping.
        :param base_pause: Average seconds to wait between scrolls for network hydration.
        """
        if not self.driver:
            raise Exception("Browser is not running! Start the browser before scrolling.")

        print(f"[+] Starting infinite scroll sequence (Max passes: {max_scrolls})...")
        
        # Get initial scroll height of the document using CDP JavaScript evaluation
        last_height = self.driver.evaluate("document.body.scrollHeight")
        
        for pass_num in range(1, max_scrolls + 1):
            print(f"  -> Scroll pass {pass_num}/{max_scrolls}...")
            
            # 1. Scroll down to the bottom of the currently rendered DOM
            self.driver.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            
            # 2. Add randomized human timing so rate-limiters don't flag fixed intervals
            sleep_time = base_pause + random.uniform(-0.5, 1.2)
            self.driver.sleep(max(1.0, sleep_time))
            
            # 3. Check the new document height after waiting for API hydration
            new_height = self.driver.evaluate("document.body.scrollHeight")
            
            # 4. If the height didn't change, perform a "wiggle scroll" to unstick lazy loaders
            if new_height == last_height:
                print("  [!] Page height unchanged. Attempting scroll wiggle...")
                # Scroll up slightly, wait, then scroll back down
                self.driver.evaluate("window.scrollBy(0, -400);")
                self.driver.sleep(1.0)
                self.driver.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                self.driver.sleep(2.0)
                
                new_height = self.driver.evaluate("document.body.scrollHeight")
                
                # If it is STILL unchanged, we have hit the true bottom of the feed
                if new_height == last_height:
                    print(f"[SUCCESS] Reached the end of the product feed at pass {pass_num}.")
                    break
            
            last_height = new_height
            
        print("[+] Infinite scroll sequence complete.")

    def stop(self):
        if self.driver:
            print("[+] Closing browser session...")
            self.driver.quit()
            self.driver = None

# =====================================================================
# INSTANT TEST BLOCK
# Run this file directly from your terminal to test Step 1!
# =====================================================================
if __name__ == "__main__":
    print("--- Starting Step 1: Browser Initialization Test ---")
    
    # We keep headless=False so you can watch the browser launch and navigate
    browser = StealthBrowser(headless=False)
    
    try:
        # httpbin safely echoes back the headers your browser is sending to servers
        test_url = "https://httpbin.org/headers"
        browser.get(test_url)
        
        # Extract the page text directly using CDP
        content = browser.driver.get_text("body")
        print("\n[SUCCESS] Page loaded! Here are the headers your browser sent:")
        print("------------------------------------------------------------")
        print(content.strip()[:400] + "\n...\n")
        print("------------------------------------------------------------")
        
        # Keep the window open for 3 seconds so you can see it in action
        browser.driver.sleep(3)
        
    except Exception as e:
        print(f"\n[ERROR] Step 1 Test Failed: {e}")
        
    finally:
        browser.stop()
        print("--- Step 1 Test Complete ---")