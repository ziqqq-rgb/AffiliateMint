"""
Wraps the scraper as a FastMCP tool so it can be called the same way
whether it's triggered by cron, by the dashboard's "run now" button
(FR-1.5), or from a dev workbench like Claude or Cursor (design doc,
section 3.2 - "Portability").
"""

from fastmcp import FastMCP

from scraper.run import scrape_products_from_latest_capture

mcp = FastMCP("tiktok-scraper")


@mcp.tool()
def run_scraper() -> list[dict]:
    """Parse the most recently captured TikTok Shop session and return the
    shortlisted products.

    FR-1.1: this reads whatever was last saved by
    `python -m scraper.capture_session` - a human has to run that
    manually first (TikTok blocks fully automated browsing), so this
    tool covers the deterministic parse + filter half of the pipeline,
    not live scraping on demand.
    """
    return scrape_products_from_latest_capture()


if __name__ == "__main__":
    mcp.run()
