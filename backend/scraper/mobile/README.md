# Mobile scraper (Appium + OCR)

An alternative to `scraper/` (the Playwright web scraper) for the
parts of TikTok Shop that only exist inside the real, installed app -
most affiliates find commission %, stock, and product search live in
the app itself, not on any page a browser can reach.

## Two ways to run it

- **`scrape.py`** - you manually navigate to the screen you want
  scraped, press Enter, it OCRs whatever's on screen.
- **`scrape_interactive.py`** - you open the Product Ranking screen
  once, then everything after that is autonomous: it discovers the
  category tabs and section names by OCR, sends them to you on
  Telegram to pick from, taps/scrolls its way there on its own, then
  scrapes the result. No more manual taps after the first screen.

Both share the same OCR/extraction engine (`ocr.py`).

## Why OCR, not element locators

The original plan here was UI element automation (find the price
element by its resource-id, read its text). That does not work on
this app: **TikTok's product-browsing screens render everything as
images/canvas, not real Android text views** - confirmed empirically
by pulling the page source on multiple screens, all zero text nodes,
only `ImageView`s. No locator, however well-tuned, can find text that
was never a text node.

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

4. **On your phone/tablet**: Settings -> About -> tap "Build number" 7
   times to unlock Developer Options, then enable USB debugging.

5. **Connect via USB**, accept the debugging prompt, confirm with:

       adb devices

6. **Install Python dependencies:**

       pip install -r scraper/mobile/requirements-mobile.txt

7. **Start the Appium server** in its own terminal and leave it running:

       appium

8. **For `scrape_interactive.py` only** - create a Telegram bot via
   [@BotFather](https://t.me/BotFather), get its token, and get your
   own chat ID (message [@userinfobot](https://t.me/userinfobot)).
   Put both in `.env` as `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

## Confirmed working device values

Found via real testing - yours should match, but confirm with
`adb shell pm list packages | grep tiktok`:

    app_package:  com.ss.android.ugc.trill
    app_activity: com.ss.android.ugc.aweme.splash.SplashActivity

(already set as the defaults in `config.py`)

**Important:** every new Appium session force-launches the app to its
home/splash screen - it can NOT resume wherever you last had it open,
even with `no_reset=True` (that only preserves login data, not your
current screen). Both scripts below account for this by pausing and
waiting for you to navigate before doing anything else.

## First run: log in

    cd backend
    python -m scraper.mobile.login_helper

Log in on your phone as normal. Session persists on-device afterwards.

## Run the manual version

    python -m scraper.mobile.scrape

Navigate to the product list you want scraped yourself, press Enter,
it screenshots and OCRs that screen.

## Run the autonomous version

    python -m scraper.mobile.scrape_interactive

Navigate to the **Product Ranking** screen (only), press Enter. It
will:
1. OCR the category tabs, text you the list, wait for your reply
2. Tap the tab you picked
3. Scroll through discovering section names ("Instant Hijab", "Nail
   Care", ...), text you that list, wait for your reply
4. Scroll back down to find and tap the one you picked
5. Screenshot and scrape the resulting product list

## Debugging a bad scrape

Don't guess - `debug_ocr.py` saves the screenshot to disk and prints
every line Tesseract found, whether or not it matched a price/earn
pattern:

    python -m scraper.mobile.debug_ocr

If cards are getting merged or split wrong, or a category isn't being
found, this is the first thing to run.

## Known limitations (read before relying on this)

- **`stock_volume` is always 0.** No screen we've tested shows a
  remaining-stock number via OCR. If `scraper/config.py`'s
  `min_stock` threshold is above 0, every OCR result gets filtered
  out. Either lower that threshold for mobile runs, or accept stock
  isn't part of this data source.
- **`review_score` is 0 on screens without a visible rating** - same
  filtering risk if `min_review_score` > 0.
- **Compressed/low-res screenshots lose words.** On a real screenshot
  passed through Telegram's JPEG compression, some tab/category words
  were dropped entirely by OCR (e.g. "Pet Supplies" read as just
  "Pet"). Screenshots pulled directly off the device (not
  re-compressed) should read more reliably.
- **When OCR only catches one price-like number for a card** (its
  actual commission text got dropped), the code deliberately reports
  `commission_rm: 0` rather than guessing - check `raw_payload` on
  that row if a result looks incomplete.
- **Title extraction picks the longest line above ~25 characters** -
  reliable for real product titles, but a stray long caption/tagline
  on the page can occasionally get picked up as a fake "product" with
  no price data; these self-filter out downstream since they always
  fail the commission-percentage threshold.
- **Tab/section discovery constants (`TAB_BAR_HEIGHT_FRACTION`,
  `WORD_GAP_TAB_BOUNDARY_PX`, `ROW_TOLERANCE_PX`, `HEADING_PROXIMITY_PX`
  in `categories.py`) were calibrated against one real 1280x800
  screenshot** - if your device's resolution or TikTok's layout
  differs meaningfully, use `debug_ocr.py`-style inspection to retune
  them.

## Risk, stated plainly (same NFR 5.2 spirit as the web scraper)

UI automation + screenshotting on a real app is generally easier for
anti-bot systems to flag than network-level scraping. Keep runs
infrequent, keep `human_delay()` calls in place, and treat this like
the design doc treats the web scraper: an accepted business risk, not
a guaranteed-safe technique.
