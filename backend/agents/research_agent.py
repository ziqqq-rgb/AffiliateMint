"""
Deep research agent - FR-2.1, FR-2.2.

Builds one research dossier per scraped product. Grounds the prompt
in the product's own scraped data (title, raw payload) so Hermes
isn't inventing facts from general knowledge - FR-2.2.
"""

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

Return JSON with exactly these keys:
what_it_does, key_benefits (list of 3-5 strings), usp,
review_summary_positive, review_summary_negative.
"""


def build_research_dossier(product: ScrapedProduct) -> dict:
    prompt = RESEARCH_PROMPT_TEMPLATE.format(
        title=product.title,
        price_rm=product.price_rm,
        review_score=product.review_score,
        review_count=product.review_count,
        units_sold=product.units_sold,
        raw_payload=product.raw_payload,
    )
    return run_task(prompt, expects_json=True)
