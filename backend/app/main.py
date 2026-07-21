"""
FastAPI application entrypoint.

Wires routers together and creates DB tables on startup. It does not
contain business logic itself (see app/services/) or DB details (see
app/db.py). Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
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

app.include_router(products.router)
app.include_router(research.router)
app.include_router(scripts.router)
app.include_router(cards.router)
app.include_router(earnings.router)
app.include_router(scraper.router)

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
