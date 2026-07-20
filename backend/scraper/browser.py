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
        Scrolls BOTH the main window and any internal scrollable div containers
        (like TikTok Shop's inner product grids) to trigger Intersection Observers.
        """
        if not self.driver:
            raise Exception("Browser is not running! Start the browser before scrolling.")

        print(f"[+] Starting deep container scroll sequence (Max passes: {max_scrolls})...")
        
        for pass_num in range(1, max_scrolls + 1):
            print(f"  -> Scroll pass {pass_num}/{max_scrolls}...")
            
            # 1. JavaScript that hunts for ALL scrollable containers on the page and scrolls them!
            deep_scroll_js = """
            (() => {
                // Scroll the main window
                window.scrollBy(0, window.innerHeight * 0.8);
                
                // Find and scroll all internal containers (like TikTok's product feed wrapper)
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.scrollHeight > el.clientHeight + 50) {
                        const style = window.getComputedStyle(el);
                        if (['auto', 'scroll'].includes(style.overflowY) || ['auto', 'scroll'].includes(style.overflow)) {
                            el.scrollBy(0, el.clientHeight * 0.8);
                        }
                    }
                }
            })();
            """
            
            # Execute 3 incremental scroll bursts per pass
            for _ in range(3):
                self.driver.evaluate(deep_scroll_js)
                self.driver.sleep(0.5)
                
            # 2. Add randomized human pause for API packets to hydrate
            sleep_time = base_pause + random.uniform(-0.3, 0.8)
            self.driver.sleep(max(1.0, sleep_time))
            
        print("[+] Deep infinite scroll sequence complete.")
        
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