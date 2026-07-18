# backend/scraper/mobile/driver.py
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
    options.no_reset = True

    driver = webdriver.Remote(config.appium_server_url, options=options)
    try:
        # Force a fresh, predictable launch every run - if TikTok was
        # already running in the background from a previous session,
        # Appium can silently attach to whatever screen it was left on
        # instead of actually opening it fresh. This is what caused
        # "sometimes it opens, sometimes it doesn't."
        driver.terminate_app(config.app_package)
        time.sleep(1.0)
        driver.activate_app(config.app_package)
        time.sleep(4.0)  # let the home feed finish rendering before any tap fires

        yield driver
    finally:
        driver.quit()


def human_delay() -> None:
    """NFR 5.2-equivalent for mobile: randomized delay, not machine-regular taps."""
    time.sleep(random.uniform(config.min_delay_seconds, config.max_delay_seconds))