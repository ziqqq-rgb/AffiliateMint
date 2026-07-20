# Backend

FastAPI service that implements the pipeline described in
`docs/TikTok_Affiliate_AI_Engine_Requirements_Design.md`.

## Layout

    app/
      routers/      HTTP layer only - no business logic
      services/      business logic (pipeline.py = the state machine, feedback.py = earnings)
      mcp_tools/      FastMCP tool wrappers (dashboard "run now" / dev workbench access)
      models.py       SQLModel tables (doubles as Pydantic schemas)
      config.py       the only file that reads environment variables
      db.py           engine/session setup only
    scraper/          Playwright scraper for TikTok Shop's public storefront (NFR 5.5)
    agents/           Hermes Agent wrappers: research, script, memory
    tests/            pytest, no live network/Hermes required

## Run locally

    pip install -r requirements.txt
    playwright install chromium
    cp .env.example .env      # then fill in HERMES_API_URL / HERMES_API_KEY
    uvicorn app.main:app --reload

Run tests with `pytest`.

## How the scraper works

`scraper/run.py` drives a real Playwright browser to
`shop.tiktok.com/my` and listens for the product-feed network response
(`scraper/intercept.py`) instead of building the request by hand -
TikTok's own page JS constructs and signs it; we just read what comes
back. See `scraper/config.py` for the endpoint pattern currently
captured, and `scraper/login_helper.py` if you need to open a visible
browser to find a *different* page's endpoint (only the homepage feed
is wired up today - a category or search page would need its own
capture, same process).

No commission data is available on the public storefront - that only
exists behind TikTok's Seller/Affiliate Center login. The pipeline
shortlists on rating and units sold instead
(`scraper/filters.py`).

## What's stubbed vs real

- `scraper/config.py`'s `target_endpoint_pattern` only covers the
  homepage product feed - it isn't scoped to a search term or
  category yet. Capturing a category/search page's endpoint (same
  DevTools process as before) and wiring it into `scraper/run.py` is
  the natural next step for targeted scraping.
- `agents/hermes_client.py` expects a running Hermes Agent instance at
  `HERMES_API_URL` - point it at wherever you host Hermes.
- Everything else (state machine, DB schema, API routes, tests) is
  real and runs today.

## Why no scraping "AI agent"

Extraction here is a deterministic parsing problem (JSON in, dict
out) - `scraper/intercept.py` maps known fields directly, no LLM
involved. Hermes is reserved for the reasoning-heavy stages further
down the pipeline (research dossier, script writing), matching design
doc 3.2's "deterministic execution" principle: the more of the
pipeline that's plain code instead of a model call, the more of it is
fast, free, and predictable.
