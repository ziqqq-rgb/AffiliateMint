"""
Wraps the scraper as a FastMCP tool so it can be called the same way
whether it's triggered by cron, by the dashboard's "run now" button
(FR-1.5), or from a dev workbench like Claude or Cursor (design doc,
section 3.2 - "Portability").
"""

from fastmcp import FastMCP

from scraper.run import scrape_products

mcp = FastMCP("tiktok-scraper")


@mcp.tool()
def run_scraper(category: str, shortlist_size: int = 5) -> list[dict]:
    """Scrape TikTok Shop Malaysia for one category and return the shortlisted products.

    FR-1.1, FR-1.3, FR-1.5: live product search + filter rules + on-demand trigger.
    """
    return scrape_products(category=category, shortlist_size=shortlist_size)


if __name__ == "__main__":
    mcp.run()
