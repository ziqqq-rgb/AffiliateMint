"""
backend/scraper/capture_session.py
Step 2: Session and Cookie Manager for CDP Mode.
Uses SeleniumBase CDP's built-in cookie methods with positional arguments to avoid keyword traps.
"""
import os
import time
from scraper.browser import StealthBrowser

class SessionManager:
    def __init__(self, browser: StealthBrowser):
        """Connects the session manager to an active StealthBrowser instance."""
        self.browser = browser

    def save_session(self, filepath: str = "affiliate_session.txt"):
        """
        Uses SeleniumBase CDP's built-in cookie saver to store all current cookies.
        We pass filepath as a positional argument to satisfy Python's internal CookieJar.
        """
        if not self.browser.driver:
            raise Exception("Browser is not running! Start the browser before saving a session.")
        
        print(f"[+] Extracting and saving cookies from current session...")
        
        # Ensure the directory exists if a folder path was provided
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Pass directly as a positional argument!
        self.browser.driver.save_cookies(filepath)
            
        print(f"[SUCCESS] Session cookies saved to -> {filepath}")
        return filepath

    def load_session(self, domain_url: str, filepath: str = "affiliate_session.txt"):
        """
        Navigates to the domain first (required by browser security), 
        then uses CDP's built-in loader to restore the authenticated state.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Session file not found: {filepath}")
            
        if not self.browser.driver:
            self.browser.start()

        print(f"[+] Navigating to {domain_url} to establish domain origin...")
        self.browser.get(domain_url)
        
        print(f"[+] Loading session cookies from -> {filepath}")
        # Pass directly as a positional argument!
        self.browser.driver.load_cookies(filepath)
                
        print(f"[SUCCESS] Injected cookies! Refreshing page to apply session...")
        # Refresh the page so the server recognizes our newly injected cookies
        self.browser.driver.refresh()
        self.browser.driver.sleep(2)

    def interactive_login_capture(self, login_url: str, filepath: str = "affiliate_session.txt", wait_time: int = 45):
        """
        PRO-TIP: Opens a browser window and pauses so YOU can manually log in, 
        solve 2FA, or pass visual CAPTCHAs. Once time is up, it automatically 
        saves your authenticated cookies for automated scripts to use later!
        """
        if not self.browser.driver:
            self.browser.start()
            
        print(f"\n[!] OPENING INTERACTIVE LOGIN SESSION")
        print(f"[!] Please log into your account in the browser window.")
        print(f"[!] You have {wait_time} seconds before the session is automatically saved...\n")
        
        self.browser.get(login_url)
        
        # Countdown timer in the terminal
        for remaining in range(wait_time, 0, -5):
            print(f"... saving session in {remaining} seconds ...")
            time.sleep(5)
            
        self.save_session(filepath)
        print("[+] Interactive capture complete!")

# =====================================================================
# INSTANT TEST BLOCK
# Run this file directly to test CDP cookie saving and loading!
# =====================================================================
if __name__ == "__main__":
    print("--- Starting Step 2: Session & Cookie Manager Test ---")
    
    test_file = "test_affiliate_session.txt"
    browser = StealthBrowser(headless=False)
    
    try:
        browser.start()
        session = SessionManager(browser)
        
        # 1. Navigate to a URL that automatically sets a test cookie
        print("\n--- Phase 1: Setting a cookie ---")
        setup_url = "https://httpbin.org/cookies/set?affiliate_token=mint_secret_123"
        browser.get(setup_url)
        
        # 2. Save the session using positional argument
        session.save_session(test_file)
        
        # 3. Clear browser cookies
        print("\n--- Phase 2: Wiping browser cookies ---")
        browser.driver.clear_cookies()
        browser.get("https://httpbin.org/cookies")
        print("Cookies after wipe:", browser.driver.get_text("body"))
        
        # 4. Load the session back from our file!
        print("\n--- Phase 3: Restoring saved session ---")
        session.load_session(domain_url="https://httpbin.org/cookies", filepath=test_file)
        
        # Verify our affiliate_token cookie returned
        restored_content = browser.driver.get_text("body")
        print("\n[SUCCESS] Current browser cookies after loading file:")
        print("------------------------------------------------------------")
        print(restored_content.strip())
        print("------------------------------------------------------------")
        
        # Clean up our test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"[+] Cleaned up temporary test file: {test_file}")
            
        browser.driver.sleep(3)
        
    except Exception as e:
        print(f"\n[ERROR] Step 2 Test Failed: {e}")
        
    finally:
        browser.stop()
        print("--- Step 2 Test Complete ---")