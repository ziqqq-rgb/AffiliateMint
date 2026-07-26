"""
Step: does Firecrawl's /search endpoint return useful grounding context
for a specific product - the kind of thing the research agent could use
to write a real 3rd USP or spot competitor pricing, instead of just
restating the scraped rating? This never touches tiktok.com or shopee's
site directly, so it sidesteps the anti-bot problem entirely.

Requires: export FIRECRAWL_API_KEY=fc-...
Usage: python3 -m scraper.manual_test_firecrawl_search "lightweight baby stroller foldable"
"""
import os
import sys

import httpx

API_KEY = "fc-1f5ffa41ab7a494a884c0dd69b4b9674"
SEARCH_URL = "https://api.firecrawl.dev/v1/search"


def main(query: str) -> None:
    if not API_KEY:
        print("[!] Set FIRECRAWL_API_KEY first (get one free at firecrawl.dev)")
        sys.exit(1)

    response = httpx.post(
        SEARCH_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"query": query, "limit": 5, "scrapeOptions": {"formats": ["markdown"]}},
        timeout=60.0,
    )
    print(f"[status] {response.status_code}")

    body = response.json()
    if not body.get("success"):
        print(f"[FAILED] {body}")
        return

    results = body["data"]
    print(f"[+] {len(results)} results\n")

    for i, r in enumerate(results, 1):
        print(f"--- Result {i}: {r.get('title')} ---")
        print(f"url: {r.get('url')}")
        snippet = (r.get("markdown") or "")[:400]
        print(f"snippet: {snippet}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 -m scraper.manual_test_firecrawl_search "<query>"')
        sys.exit(1)
    main(" ".join(sys.argv[1:]))