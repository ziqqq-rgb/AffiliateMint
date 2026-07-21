from fastmcp import FastMCP

from app.services.scraping_pipeline import ScrapingPipelineService

mcp = FastMCP("tiktok-scraper")


@mcp.tool()
async def run_scraper(target_url: str = "https://shop.tiktok.com/my") -> dict:
    """FR-1.5: live scrape, same entry point the dashboard's 'run now' button calls."""
    return await ScrapingPipelineService.run_async_pipeline(target_url)


if __name__ == "__main__":
    mcp.run()