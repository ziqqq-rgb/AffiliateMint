# backend/app/main.py
"""
FastAPI application entrypoint.

Wires routers together and creates DB tables on startup. It does not
contain business logic itself (see app/services/) or DB details (see
app/db.py). Run with: uvicorn app.main:app --reload
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import cards, earnings, products, research, scraper, scripts

app = FastAPI(title="TikTok Shop Affiliate AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
for router in (products.router, research.router, scripts.router, cards.router, earnings.router, scraper.router):
    api_router.include_router(router)
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}