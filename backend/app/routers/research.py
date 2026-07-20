"""
backend/app/routers/research.py
Step 5: FastAPI Router exposing our CDP Scraping Pipeline as a REST API endpoint.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from backend.app.services.pipeline import ScrapingPipelineService

router = APIRouter(prefix="/api/research", tags=["Research & Scraping"])

# Request Validation Schema using Pydantic
class ScrapeRequestPayload(BaseModel):
    url: str
    session_file: Optional[str] = None
    keywords: Optional[List[str]] = ["campaign", "token", "json", "api", "affiliate", "stats"]
    headless: bool = True

@router.post("/scrape", response_model=Dict[str, Any])
async def trigger_live_scrape(payload: ScrapeRequestPayload):
    """
    Triggers an on-demand CDP scrape and returns both page metadata 
    and intercepted background API payloads cleanly to the client.
    """
    try:
        print(f"\n[API Endpoint] Received scrape request for: {payload.url}")
        
        # Call our async pipeline bridge
        results = await ScrapingPipelineService.run_async_pipeline(
            target_url=payload.url,
            session_file=payload.session_file,
            filter_keywords=payload.keywords,
            headless=payload.headless
        )
        
        if not results.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=results.get("error", "The scraping pipeline failed unexpectedly.")
            )
            
        return {
            "status": "success",
            "message": f"Successfully intercepted {results['network_data']['total_responses']} network payloads.",
            "data": results
        }
        
    except Exception as e:
        # Catch unforeseen routing errors and return a clean JSON error response
        print(f"[API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")