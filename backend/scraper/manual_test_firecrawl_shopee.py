"""
Step: can Firecrawl's managed /scrape endpoint reach a Shopee product
page and return review text? Shopee isn't on Firecrawl's known social-
media blocklist (unlike TikTok), but that's unconfirmed - this is a
one-shot check before building anything around it.

Requires: export FIRECRAWL_API_KEY=fc-...
Usage: python3 -m scraper.manual_test_firecrawl_shopee "<shopee_product_url>"
"""
import os
import sys

import httpx

API_KEY = "fc-1f5ffa41ab7a494a884c0dd69b4b9674"
SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"


def main(product_url: str) -> None:
    if not API_KEY:
        print("[!] Set FIRECRAWL_API_KEY first (get one free at firecrawl.dev)")
        sys.exit(1)

    response = httpx.post(
        SCRAPE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"url": product_url, "formats": ["markdown"]},
        timeout=60.0,
    )
    print(f"[status] {response.status_code}")

    body = response.json()
    if not body.get("success"):
        print(f"[FAILED] {body}")
        return

    markdown = body["data"]["markdown"]
    print(f"[+] Got {len(markdown)} chars of markdown\n")

    # Cheap heuristic: does the returned content actually mention reviews?
    lower = markdown.lower()
    review_hits = lower.count("review") + lower.count("rating")
    print(f"'review'/'rating' mentions in content: {review_hits}")

    print("\n--- First 1500 chars ---")
    print(markdown[:1500])
    print("--- end sample ---")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 -m scraper.manual_test_firecrawl_shopee "<shopee_product_url>"')
        sys.exit(1)
    main(sys.argv[1])