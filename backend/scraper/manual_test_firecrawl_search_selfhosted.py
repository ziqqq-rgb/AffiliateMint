"""
Step: does the SELF-HOSTED Firecrawl instance actually return real
search results, or just respond to the root health check? Self-hosted
/search scrapes Google directly without Fire-Engine's anti-bot layer
(see chat notes) - this confirms real behavior before trusting it.

Usage: python3 -m scraper.manual_test_firecrawl_search_selfhosted "lightweight baby stroller foldable"
"""
import sys

import httpx

# Change this if you exposed the API on a different port/host.
SEARCH_URL = "http://localhost:3002/v1/search"


def main(query: str) -> None:
    response = httpx.post(
        SEARCH_URL,
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
        print('Usage: python3 -m scraper.manual_test_firecrawl_search_selfhosted "<query>"')
        sys.exit(1)
    main(" ".join(sys.argv[1:]))