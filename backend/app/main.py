# backend/app/main.py
import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import cards, dashboard, earnings, products, research, scraper, scripts, shopee, threads

# Must run before any module-level `logging.getLogger(__name__)` calls
# produce output - without this, only WARNING+ shows (Python's default),
# so the deep_research_agent's "topics found for product X" INFO lines
# would be silently dropped even though the WARNING lines show fine.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="TikTok Shop Affiliate AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
for router in (
    products.router, research.router, scripts.router, cards.router,
    earnings.router, scraper.router, dashboard.router,
    shopee.router, threads.router,
):
    api_router.include_router(router)
    
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}