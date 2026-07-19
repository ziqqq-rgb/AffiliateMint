"""
Appium/device configuration for the mobile scraper.

Isolated here for the same reason as scraper/config.py (NFR 5.5):
package names, activity names, and device details are the part most
likely to need updating as TikTok ships new app builds or you switch
phones. Filter thresholds (commission %, stock, rating) are NOT
duplicated here - both the web and mobile scrapers share the same
ones from scraper/config.py, so there's one place to tune them.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MobileScraperConfig:
    appium_server_url: str = "http://127.0.0.1:4723"

    # Confirmed via real device testing (July 2026) on a Malaysian
    # TikTok install. Double-check on your own device with:
    #   adb shell pm list packages | grep tiktok
    app_package: str = "com.ss.android.ugc.trill"

    # Confirmed via: adb shell dumpsys window | grep mCurrentFocus
    # while TikTok was open on the same device.
    app_activity: str = "com.ss.android.ugc.aweme.splash.SplashActivity"

    platform_version: Optional[str] = None  # None = auto-detect from the connected device
    new_command_timeout_seconds: int = 300

    # NFR 5.2 equivalent for mobile: randomized delay between taps
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 6.0


config = MobileScraperConfig()
