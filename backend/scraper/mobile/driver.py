"""
Appium session management for the mobile scraper.

Mirrors scraper/browser.py's role for the web scraper: this is the one
place that opens/closes the connection to the device, so every other
mobile-scraper module just gets a ready `driver` to interact with.

Appium's Python client is synchronous (Selenium-style), unlike the
Playwright web scraper, so there's no async/await here on purpose.

Prerequisites (see mobile/README.md for the full walkthrough):
  1. `appium` server running in a terminal (default port 4723)
  2. A real Android phone connected via USB with Developer Mode + USB
     debugging on, visible to `adb devices`
  3. The TikTok app already installed and logged in (run
     login_helper.py first if it isn't)
"""

import random
import time
from contextlib import contextmanager

from appium import webdriver
from appium.options.android import UiAutomator2Options

from scraper.mobile.config import config


@contextmanager
def app_session():
    """Yields a ready Appium driver already attached to the TikTok app."""
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = config.app_package
    options.app_activity = config.app_activity
    if config.platform_version:
        options.platform_version = config.platform_version
    options.new_command_timeout = config.new_command_timeout_seconds
    # Attach to the app as-is - don't reinstall or wipe the session you
    # already logged into via login_helper.py.
    options.no_reset = True

    driver = webdriver.Remote(config.appium_server_url, options=options)
    try:
        yield driver
    finally:
        driver.quit()


def human_delay() -> None:
    """NFR 5.2-equivalent for mobile: randomized delay, not machine-regular taps."""
    time.sleep(random.uniform(config.min_delay_seconds, config.max_delay_seconds))
