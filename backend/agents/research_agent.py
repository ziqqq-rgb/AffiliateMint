"""
Deep research agent - FR-2.1, FR-2.2.

Builds one research dossier per scraped product. Grounds the prompt in
the product's own scraped data (title, raw payload) plus optional
market context from the open web (agents/market_context.py). Does NOT
use scraped review text - TikTok/Shopee product pages aren't reliably
reachable (confirmed via scraper/manual_test_*_reviews.py and
manual_test_firecrawl_shopee.py).
"""

from agents.market_context import build_market_context
from app.models import ScrapedProduct
from agents.providers.nvidia_client import run_task 


RESEARCH_PROMPT_TEMPLATE = """\
You are researching a TikTok Shop product for a Malaysian affiliate creator.
Base everything strictly on the data below - do not invent facts.

Product title: {title}
Price: RM{price_rm}
Rating: {review_score} ({review_count} reviews)
Units sold: {units_sold}
Raw listing data: {raw_payload}

Note: you do NOT have literal review text - only an aggregate rating and
review count. For review_summary_positive/negative, infer likely themes
from the rating, price, title, and units sold. Do not invent direct
quotes or specific claims attributed to reviewers.

External market context (general web search results about this type of
product - may contain unrelated site navigation/clutter, ignore that.
Use this ONLY for general category facts like typical price range or
common competing brands - never attribute it to THIS specific product
or claim it came from this product's own reviewers):
{market_context}

Return JSON with exactly these keys:
- what_it_does (string)
- key_benefits (list of 3-5 strings)
- usps (list of EXACTLY 3 strings). Each one must be a genuinely
  different reason to buy - draw them from different angles, e.g. one
  on price/value (use the market context's price range if available),
  one on a functional feature, one on a quality/trust signal (rating,
  units sold, discount depth). Do not submit 3 rewordings of the same
  point.
- review_summary_positive (string)
- review_summary_negative (string)
"""


def build_research_dossier(product: ScrapedProduct) -> dict:
    market_context = build_market_context(product) or "No external context available."

    prompt = RESEARCH_PROMPT_TEMPLATE.format(
        title=product.title,
        price_rm=product.price_rm,
        review_score=product.review_score,
        review_count=product.review_count,
        units_sold=product.units_sold,
        raw_payload=product.raw_payload,
        market_context=market_context,
    )
    return run_task(prompt, expects_json=True)