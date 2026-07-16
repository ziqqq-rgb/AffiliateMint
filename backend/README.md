# Backend

FastAPI service that implements the pipeline described in
`docs/TikTok_Affiliate_AI_Engine_Requirements_Design.md`.

## Layout

    app/
      routers/     HTTP layer only - no business logic
      services/     business logic (pipeline.py = the state machine, feedback.py = earnings)
      models.py     SQLModel tables (doubles as Pydantic schemas)
      config.py     the only file that reads environment variables
      db.py         engine/session setup only
    scraper/         Playwright scraper, isolated on purpose (NFR 5.5)
    agents/           Hermes Agent wrappers: research, script, memory
    tests/            pytest, no live network/Hermes required

## Run locally

    pip install -r requirements.txt
    playwright install chromium
    cp .env.example .env      # then fill in HERMES_API_URL / HERMES_API_KEY
    uvicorn app.main:app --reload

Run tests with `pytest`.

## What's stubbed vs real

- `scraper/config.py` and `scraper/intercept.py` - the endpoint pattern
  and field names are placeholders. Open TikTok Shop's Network tab
  yourself and fill in the real values (design doc FR-1.1, FR-1.2).
- `agents/hermes_client.py` expects a running Hermes Agent instance at
  `HERMES_API_URL` - point it at wherever you host Hermes.
- Everything else (state machine, DB schema, API routes, tests) is
  real and runs today.
