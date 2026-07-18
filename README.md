# TikTok Shop Affiliate AI Engine

Full project scaffold matching `docs/TikTok_Affiliate_AI_Engine_Requirements_Design.md`.

- `backend/` - FastAPI + SQLModel + Playwright scraper + Hermes Agent wrappers
- `frontend/` - React (Vite) + Tailwind dashboard

## Run order

1. `cd backend && pip install -r requirements.txt && playwright install chromium`
2. `cp backend/.env.example backend/.env` and fill in your Hermes Agent URL/key
3. `cd backend && uvicorn app.main:app --reload` (serves on :8000)
4. `cd frontend && npm install && npm run dev` (serves on :5173, proxies /api to :8000)

## What's real vs stubbed

Verified working in this scaffold:
- Full DB schema (SQLModel) matching design doc section 6
- The pipeline state machine (`backend/app/services/pipeline.py`) - unit
  tested in `backend/tests/`, passes today
- All REST routes wired and tested end-to-end
- Frontend Kanban board, API client, and components - type-checks clean

Deliberately left as TODOs, because only you can fill them in:
1. `backend/scraper/config.py` + `scraper/intercept.py` - the real
   TikTok Shop network endpoint pattern and response field names.
   Capture these yourself from the browser Network tab.
2. `backend/agents/hermes_client.py` - point `HERMES_API_URL` at your
   running Hermes Agent instance.

## Two scraper implementations

TikTok Shop's affiliate product search often lives inside the native
app, not any page a browser can reach - so there are two scrapers,
pick whichever matches where you actually find products:

- `backend/scraper/` - Playwright, intercepts network responses from
  a browser. Use this if your product search works on the mobile web
  or desktop site.
- `backend/scraper/mobile/` - Appium, reads the real TikTok app on a
  connected Android phone via UI automation. See
  `backend/scraper/mobile/README.md` for full setup (Appium server,
  ADB, Appium Inspector to find element IDs). Use this if product
  search only works in the installed app.

Both return the same shape (a plain list of product dicts) and share
the same filter rules in `scraper/filters.py`, so
`app/mcp_tools/scraper_tool.py` can be pointed at either one.

## Folder map

    backend/
      app/
        routers/      HTTP layer only, no business logic
        services/      pipeline.py = the state machine, feedback.py = earnings loop
        models.py       SQLModel tables (also the API schemas)
        config.py       only file that reads environment variables
        db.py            engine/session setup only
        mcp_tools/       scraper wrapped as a FastMCP tool
      scraper/           Playwright scraper, isolated (NFR 5.5)
      agents/             Hermes wrappers: research, script, memory (FTS5 ledger)
      tests/               pytest, no live network/Hermes required
    frontend/
      src/
        components/       KanbanBoard, ContentCard, TeleprompterView, EarningsForm
        api.ts             single API client
        types.ts            mirrors backend/app/models.py
