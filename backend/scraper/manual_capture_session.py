# scraper/manual_capture_session.py
"""Run once to capture a real browsing session's cookies for run.py to
reuse - avoids hitting TikTok with fresh incognito every scrape.

Usage: python3 -m scraper.manual_capture_session
"""
from seleniumbase import Driver
from scraper.session_store import save_cookies

driver = Driver(uc=True, incognito=False, headless=False)
try:
    driver.get("https://shop.tiktok.com/my")
    print("[!] Browse normally for 45s - click a category, scroll, log in if you want.")
    driver.sleep(45)
    save_cookies(driver, "affiliate_session.txt")
finally:
    driver.quit()