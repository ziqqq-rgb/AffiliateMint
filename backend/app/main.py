import asyncio

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import cards, dashboard, earnings, products, research, scraper, scripts, shopee, threads
from app.services.scheduler import run_scheduler_loop


app = FastAPI(title="TikTok Shop Affiliate AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
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
async def on_startup():
    init_db()
    asyncio.create_task(run_scheduler_loop())  # Post Queue background poller


@app.get("/health")
def health():
    return {"status": "ok"}