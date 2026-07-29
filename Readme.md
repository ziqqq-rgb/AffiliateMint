# AffiliateMint

Affiliate marketing automation for TikTok Shop and Shopee, built for the Malaysian market.

AffiliateMint scrapes trending products, researches them with AI, writes scripts and posts, and publishes them — while a human stays in control of what actually goes out. It's a solo project built to handle the repetitive parts of affiliate content creation: finding products, writing about them, and posting on a schedule.

## The problem

Running affiliate content by hand means the same loop every day: browse TikTok Shop or Shopee for products worth promoting, look up what makes them worth buying, write a hook and caption, and post at the right time. None of that is hard on its own, but doing it for dozens of products a week adds up fast.

AffiliateMint automates that loop end to end, while keeping every generated script and post editable before anything goes live.

## How it works

```
Scrape products (TikTok Shop / Shopee)
        │
        ▼
AI research dossier (USPs, benefits, review summary)
        │
        ▼
Script generation (TikTok) / Post generation (Shopee → Threads)
        │
        ▼
Review & edit (optional)
        │
        ▼
Publish now, or schedule for later
        │
        ▼
Feedback loop: edits and earnings shape future generations
```

1. **Scrape** — a hybrid SeleniumBase + Playwright scraper pulls product data (price, rating, units sold, commission) straight from the storefront's own network traffic, not the rendered page.
2. **Research** — an AI agent builds a short dossier per product: what it does, three distinct selling points, and a review summary, grounded in the scraped data plus live web search for market context.
3. **Deep research** — for products with something worth digging into (an ingredient, a fabric, a certification, a design's heritage), a second pass researches that specific angle and adds sourced detail.
4. **Generate** — TikTok products get three script angles (problem hook, tech spec, lifestyle). Shopee products get three short Threads post variations in Bahasa Malaysia.
5. **Review** — every script and post can be hand-edited before it goes out. Edits get logged and used to steer future generations toward what's actually being kept.
6. **Publish** — post immediately, or drop it into a queue with a specific time slot. A background scheduler checks every minute for anything due.
7. **Learn** — logged earnings and manual edits are stored in a local memory ledger, and future scripts/posts search that history for what's worked before.

## Features

- Kanban board to review scraped products before committing time to them
- One-click pipeline: research and script/post generation in a single background job
- Deep research section for ingredient, material, or heritage-level detail
- Inline editing for scripts and posts, with edits feeding back into the learning loop
- Post queue with a time-slot picker and a self-healing scheduler (survives restarts)
- Manual earnings logging, with reminders for posted content that hasn't been checked yet
- Simple analytics: posts per day, 7-day trend, split by platform

## Tech stack

**Backend**
- FastAPI + SQLModel on SQLite (with an FTS5 full-text index for the memory ledger)
- Plain `asyncio` background tasks for the queue scheduler — no Celery, Redis, or cron

**Scraping**
- SeleniumBase (undetected Chrome mode) + Playwright connected over CDP
- Cookie session persistence, so a run doesn't have to fight anti-bot checks from scratch every time

**AI**
- GLM-5.2 (via NVIDIA NIM) for research and deep research
- Gemini 2.5 Flash (via Google AI Studio) for scripts and Threads posts
- Hermes (Nous Research), running locally, for the memory and feedback loop
- Self-hosted Firecrawl for web search grounding

**Frontend**
- React + TypeScript + Vite + Tailwind CSS

**Publishing**
- Meta Threads API, with automatic retry on transient failures

## Project structure

```
backend/
├── agents/                # AI agent logic: research, scripts, threads, memory
│   └── providers/         # Thin HTTP clients per provider (NVIDIA, Gemini, Firecrawl, Hermes)
├── app/
│   ├── routers/            # FastAPI route handlers — HTTP only, no business logic
│   ├── services/            # Business logic and state machines (pipeline, scheduler, etc.)
│   ├── mcp_tools/            # MCP tool exposure for the scraper
│   ├── models.py              # Database tables
│   ├── schemas.py              # API response shapes that aren't 1:1 with a table
│   ├── config.py                # All environment variables, read in one place
│   ├── db.py                     # Engine and session setup
│   └── main.py                    # App entry point
├── scraper/
│   ├── shopee/                    # Shopee scraper (mirrors the TikTok scraper's shape)
│   └── ...                         # TikTok Shop scraper: browser, navigation, parsing
└── tests/

frontend/
└── src/
    ├── components/            # UI components, one file per component
    ├── lib/                    # Pure helper functions (formatting, date grouping, etc.)
    ├── api.ts                   # Every backend call, in one place
    └── types.ts                  # Shared TypeScript types
```

## Getting started

### Prerequisites

- Python 3.11+
- Node 18+
- A running Hermes agent (local inference server) on port 9119
- A Firecrawl instance (self-hosted or hosted)
- API keys for NVIDIA NIM and Google AI Studio
- A Meta Threads API access token (only needed if you're publishing Shopee posts to Threads)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env    # fill in your API keys and endpoints
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite connection string |
| `HERMES_API_URL` | Local Hermes agent endpoint |
| `NVIDIA_API_KEY`, `NVIDIA_API_BASE` | Research agent (GLM-5.2) |
| `GEMINI_API_KEY`, `GEMINI_API_BASE` | Script and Threads agent |
| `FIRECRAWL_API_BASE`, `FIRECRAWL_API_KEY` | Web search grounding |
| `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN` | Publishing to Threads |
| `AUTO_PUBLISH_SHOPEE_THREADS` | Skip manual review and auto-publish Shopee posts |

### Tests

```bash
cd backend
python -m pytest
```

## A few design decisions worth explaining

- **No Celery or Redis.** The post queue is a single `asyncio` loop that polls for due posts once a minute. For a one-person, single-instance app, that's simpler to run and debug than adding a task broker, and it survives restarts fine since it checks by absolute due time instead of a fired timer.
- **SQLite, not Postgres.** The app runs on one machine for one operator, so the extra setup isn't worth it yet. `db.py` stays deliberately thin so swapping in Postgres later won't touch anything else.
- **Cookie sessions instead of fighting CAPTCHAs.** TikTok's anti-bot system blocks fresh browser sessions at the network level, even when a human solves the CAPTCHA. Saving and reusing a logged-in session's cookies turned out to be the reliable fix.
- **Deep research is additive, never destructive.** Scraped price, rating, and sales data is never overwritten by AI-generated content — the two live in separate fields, so a bad research run can't corrupt real data.

## Roadmap

- Allow editing scripts and posts after they've already been published
- Keep tuning topic extraction for the deep research module, especially for fashion and cultural products
- Clean up scraper parsing code that's currently duplicated across two files

## License

MIT