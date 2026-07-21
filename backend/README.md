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

The scraper drives a real Chromium session via SeleniumBase's CDP/UC mode (anti-bot resistant) and attaches Playwright over the same CDP connection to read network traffic. It combines two capture methods: a network wiretap that inspects every JSON response for product-shaped objects, and a DOM fallback that reads whatever's visibly rendered. This runs directly against shop.tiktok.com — no mobile app, no Appium, no OCR. That approach was tried and dropped: TikTok's mobile app renders product screens as canvas with zero text nodes, making element-based or OCR automation fragile and slow by comparison. The web storefront has a real DOM and real network responses, which is strictly easier to work with.

As before: no commission data exists on the public storefront (that's behind the Seller/Affiliate Center login), so shortlisting still ranks on rating + units sold.

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
