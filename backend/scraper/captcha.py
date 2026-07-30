"""
backend/scraper/captcha.py

Visible-CAPTCHA detection for TikTok Shop's storefront. Split out of
scraper/run.py so the DOM/text signals it checks for have one place to
update if TikTok changes their CAPTCHA markup.
"""

CAPTCHA_CHECK_JS = """
(() => {
    const modal = document.querySelector('#secsdk-captcha-drag-wrapper, .captcha_verify_container, [id*="captcha-drag"]');
    if (modal && modal.offsetWidth > 0 && modal.offsetHeight > 0) return true;
    const bodyText = document.body ? document.body.textContent : "";
    return bodyText.includes("Verify to continue") || bodyText.includes("Slide to verify");
})();
"""


def is_captcha_visible(driver) -> bool:
    """True if a solvable CAPTCHA modal is currently on screen."""
    return driver.execute_script(CAPTCHA_CHECK_JS)
