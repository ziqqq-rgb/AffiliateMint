# Mobile scraper (Appium + OCR)

An alternative to `scraper/` (the Playwright web scraper) for the
parts of TikTok Shop that only exist inside the real, installed app -
most affiliates find commission %, stock, and product search live in
the app itself, not on any page a browser can reach.

## Why OCR, not element locators

The original plan here was UI element automation (find the price
element by its resource-id, read its text - same idea as the web
scraper's network interception). That does not work on this app:
**TikTok's product-browsing screens render everything as images/canvas,
not real Android text views.** Confirmed empirically by pulling the
page source on two different screens (Discover search grid, Product
ranking) - both came back with zero text nodes, only `ImageView`s.
No locator, however well-tuned, can find text that was never a text
node.

Instead, `ocr.py` reads the screen the way a person would: screenshot
-> Tesseract text recognition on the actual pixels -> regex out
price/commission/sold from what it reads. This works regardless of
how the screen is rendered, but it's a fundamentally fuzzier approach
than reading structured data - see "Known limitations" below.

## One-time setup

1. **Install Node.js**, then the Appium server itself:

       npm install -g appium
       appium driver install uiautomator2

2. **Install Android platform-tools** (gives you `adb`):
   - macOS: `brew install android-platform-tools`
   - Windows/Linux: https://developer.android.com/tools/releases/platform-tools

3. **Install Tesseract** (the actual OCR engine - `pytesseract` is
   just a Python wrapper around it, it does nothing on its own):
   - macOS: `brew install tesseract`
   - Windows/Linux: https://github.com/tesseract-ocr/tesseract#installing-tesseract

4. **On your phone**: Settings -> About phone -> tap "Build number" 7
   times to unlock Developer Options, then Settings -> Developer
   options -> enable USB debugging.

5. **Connect your phone via USB**, accept the "Allow USB debugging?"
   prompt on the phone, then confirm it's visible:

       adb devices

6. **Install Python dependencies:**

       pip install -r scraper/mobile/requirements-mobile.txt

7. **Start the Appium server** in its own terminal and leave it running:

       appium

## Confirmed working device values

Found via real testing on a Malaysian TikTok install - yours should
match, but confirm with `adb shell pm list packages | grep tiktok`:

    app_package:  com.ss.android.ugc.trill
    app_activity: com.ss.android.ugc.aweme.splash.SplashActivity

(already set as the defaults in `config.py`)

## First run: log in

    cd backend
    python -m scraper.mobile.login_helper

Log in on your phone as normal. Session persists on-device afterwards.

## Run the scraper

Unlike the web scraper, this does **not** search or navigate for you
- OCR can't reliably find a search box it can't read either. Manually
open the product list you want on your phone first (e.g. TikTok's
"Product ranking" screen), THEN run:

    python -m scraper.mobile.scrape

## Known limitations (read before relying on this)

- **`stock_volume` is always 0.** Neither screen we tested shows a
  remaining-stock number via OCR. If `scraper/config.py`'s
  `min_stock` threshold is above 0, every OCR result will get
  filtered out silently failing `apply_filters()`. Either lower that
  threshold for mobile runs, or accept stock isn't part of this data
  source.
- **`review_score` is 0 on screens without a visible rating** (e.g.
  "Product ranking" doesn't show star ratings; the Discover grid
  does). Same filtering risk as above if `min_review_score` > 0.
- **Card grouping is a position-based guess** (`ROW_GROUPING_PX` in
  `ocr.py`), not real structure. If cards get merged or split
  incorrectly on your screen resolution, tune that constant.
- **Title extraction is a rough heuristic** (longest non-numeric line
  near the price) - expect it to be wrong sometimes. Everything else
  (price, commission, sold count, rating) is regex-matched directly
  and is reliable when OCR reads the text correctly.
- **OCR misreads happen** - "RM" can become "RN", commas/decimals can
  get dropped. `raw_payload` on every product keeps the full raw OCR
  text specifically so you can debug misreads without re-scraping.

## Risk, stated plainly (same NFR 5.2 spirit as the web scraper)

UI automation + screenshotting on a real app is generally easier for
anti-bot systems to flag than network-level scraping. Keep runs
infrequent, keep `human_delay()` calls in place, and treat this like
the design doc treats the web scraper: an accepted business risk, not
a guaranteed-safe technique.
