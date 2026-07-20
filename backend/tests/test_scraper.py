"""
Unit tests for the pure, I/O-free scraper logic: response parsing and
shortlist filtering. No Playwright/browser/network needed - these
just feed dicts in and check dicts out.
"""

from scraper.filters import apply_filters
from scraper.intercept import parse_response


def _raw_response(**item_overrides) -> dict:
    item = {
        "product_id": "123",
        "title": "Test Product",
        "image": {"url_list": ["https://example.com/img.webp"]},
        "product_price_info": {"sale_price_decimal": "11.86", "origin_price_decimal": "16.90"},
        "rate_info": {"score": 4.8, "review_count": "37135"},
        "sold_info": {"sold_count": 234442},
        "seller_info": {"shop_name": "TestShop"},
        "seo_url": {"canonical_url": "https://shop.tiktok.com/my/pdp/test/123"},
    }
    item.update(item_overrides)
    return {"code": 0, "message": "success", "data": {"productList": [item]}}


def test_parse_response_extracts_expected_fields():
    parsed = parse_response(_raw_response())

    assert len(parsed) == 1
    product = parsed[0]
    assert product["tiktok_product_id"] == "123"
    assert product["title"] == "Test Product"
    assert product["price_rm"] == 11.86
    assert product["original_price_rm"] == 16.90
    assert product["review_score"] == 4.8
    assert product["review_count"] == 37135
    assert product["units_sold"] == 234442
    assert product["shop_name"] == "TestShop"
    assert product["image_url"] == "https://example.com/img.webp"
    assert product["product_url"] == "https://shop.tiktok.com/my/pdp/test/123"


def test_parse_response_handles_missing_fields_gracefully():
    raw = {"code": 0, "data": {"productList": [{"product_id": "1", "title": "Bare item"}]}}
    parsed = parse_response(raw)

    assert parsed[0]["price_rm"] == 0.0
    assert parsed[0]["units_sold"] == 0
    assert parsed[0]["image_url"] == ""


def test_apply_filters_ranks_by_units_sold_and_respects_thresholds():
    products = [
        {"review_score": 4.5, "units_sold": 50},   # below min_units_sold
        {"review_score": 3.0, "units_sold": 5000},  # below min_review_score
        {"review_score": 4.9, "units_sold": 300},
        {"review_score": 4.2, "units_sold": 9000},
    ]

    shortlist = apply_filters(products)

    assert [p["units_sold"] for p in shortlist] == [9000, 300]
