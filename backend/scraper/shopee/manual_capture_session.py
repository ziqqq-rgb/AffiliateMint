"""Run once to capture a logged-in affiliate.shopee.com.my session.
Usage: python3 -m scraper.shopee.manual_capture_session"""
from seleniumbase import Driver
from scraper.session_store import save_cookies
from scraper.shopee.config import config

driver = Driver(uc=True, incognito=False, headless=False)
try:
    driver.get(config.offer_page_url)
    print("[!] Log in and land on Product Offer. 45s to save session...")
    driver.sleep(45)
    save_cookies(driver, "shopee_affiliate_session.txt")
finally:
    driver.quit()