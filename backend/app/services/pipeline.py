"""
backend/app/services/pipeline.py
Step 5: Service layer bridging FastAPI endpoints with the synchronous CDP Scraper Engine.
Uses thread pool offloading to protect the async event loop.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.scraper.run import AffiliateScraperEngine

logger = logging.getLogger(__name__)

class ScrapingPipelineService:
    @staticmethod
    def _execute_sync_scrape(
        target_url: str,
        session_file: Optional[str] = None,
        filter_keywords: Optional[List[str]] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronous worker that spins up the engine, executes the scrape, 
        and guarantees browser cleanup even if a crash occurs.
        """
        print(f"[Pipeline Worker] Launching engine for -> {target_url}")
        # We default to headless=True in production web services!
        engine = AffiliateScraperEngine(headless=headless, incognito=True)
        try:
            results = engine.run_pipeline(
                target_url=target_url,
                session_file=session_file,
                filter_keywords=filter_keywords
            )
            return results
        except Exception as e:
            logger.error(f"Scrape worker failed for {target_url}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Guarantee that zombie Chromium processes are NEVER left behind in production
            engine.close()

    @classmethod
    async def run_async_pipeline(
        cls,
        target_url: str,
        session_file: Optional[str] = None,
        filter_keywords: Optional[List[str]] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Async entry point called by FastAPI routers or AI agents.
        Offloads the blocking Chromium execution to an independent background thread.
        """
        print(f"[Pipeline Async] Offloading scraping task to worker thread...")
        
        # asyncio.to_thread runs our synchronous engine in a separate thread pool,
        # allowing FastAPI to handle hundreds of other API requests while Chrome works!
        result = await asyncio.to_thread(
            cls._execute_sync_scrape,
            target_url=target_url,
            session_file=session_file,
            filter_keywords=filter_keywords,
            headless=headless
        )
        
        return result
    
import json

def parse_tiktok_shop_item(item: dict) -> dict:
    """
    Takes a single raw product item from TikTok Shop's intercepted JSON API payload
    and maps it to our clean ScrapedProduct schema.
    """
    # Helper to safely dig into nested dictionaries without crashing if a key is missing
    price_info = item.get("product_price_info", {})
    rate_info = item.get("rate_info", {})
    sold_info = item.get("sold_info", {})
    seller_info = item.get("seller_info", {})
    seo_url = item.get("seo_url", {})
    image_data = item.get("image", {})
    
    # Extracting the first image URL safely
    url_list = image_data.get("url_list", [])
    first_image = url_list[0] if url_list else None

    # Mapping exact fields from your specification table!
    scraped_product = {
        "product_id": item.get("product_id"),
        "title": item.get("title"),
        
        # Convert string decimals to floats for Malaysian Ringgit (RM)
        "price_rm": float(price_info.get("sale_price_decimal", 0.0)),
        "original_price_rm": float(price_info.get("origin_price_decimal", 0.0)) if price_info.get("origin_price_decimal") else None,
        
        # Ratings and review counts
        "review_score": float(rate_info.get("score", 0.0)) if rate_info.get("score") else None,
        "review_count": int(rate_info.get("review_count", 0)),
        
        # Sales and seller info
        "units_sold": sold_info.get("sold_count"),
        "shop_name": seller_info.get("shop_name"),
        
        # URLs
        "product_url": seo_url.get("canonical_url"),
        "image_url": first_image,
        
        # Store the complete unaltered payload just in case you need extra fields later
        "raw_payload": json.dumps(item)
    }
    
    return scraped_product

