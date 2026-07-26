"""Shared formatting helpers for turning a ResearchDossier's JSON fields
into prompt-ready text. Used by both script_agent.py (TikTok) and
threads_agent.py (Shopee) so the same dossier renders identically
regardless of which platform's prompt is asking for it."""
import json

from app.models import ResearchDossier


def format_usps(dossier: ResearchDossier) -> str:
    """usps is a JSON-encoded list of 3 strings - render as bullets."""
    return "\n".join(f"- {usp}" for usp in json.loads(dossier.usps))


def format_deep_research(dossier: ResearchDossier) -> str:
    """ingredients_research is a JSON-encoded list of topic dossiers
    (see agents/deep_research_agent.py) - covers ingredients, material
    tech, brand/model heritage, or certifications, whichever fits the
    product. Renders as short blocks, or a plain fallback line if the
    product had nothing worth deep-researching."""
    topics = json.loads(dossier.ingredients_research or "[]")
    if not topics:
        return "No deep research available for this product."
    return "\n\n".join(
        f"{t['topic']}: {t['what_it_is']} {t['how_it_works']} Relevant to: {t['who_benefits']}"
        for t in topics
    )