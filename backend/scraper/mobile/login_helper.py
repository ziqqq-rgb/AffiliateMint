"""
Manual login helper for the mobile scraper - the Appium equivalent of
scraper/login_helper.py.

Launches the real TikTok app on your connected phone through Appium
and then just waits, so you can log in with your thumb exactly like
you always do (password, QR, SMS - whatever you normally use).
Because this attaches to your actual device rather than a fresh
install, the session persists in the app itself afterwards - future
automated runs open already logged in.

Usage:
    cd backend
    python -m scraper.mobile.login_helper
"""

from appium import webdriver
from appium.options.android import UiAutomator2Options

from scraper.mobile.config import config


def main() -> None:
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = config.app_package
    options.app_activity = config.app_activity
    if config.platform_version:
        options.platform_version = config.platform_version
    options.no_reset = True  # keep whatever's already on the device

    driver = webdriver.Remote(config.appium_server_url, options=options)

    print("\nTikTok is now open on your phone.")
    print("Log in as you normally would - this is your real device, real app.")
    print("Once you're on your normal feed/home screen, come back here.")
    input("Press Enter to end this session (your login stays saved on the device)...\n")

    driver.quit()


if __name__ == "__main__":
    main()
