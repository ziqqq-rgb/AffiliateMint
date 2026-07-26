"""
Script writing agent - FR-3.1 - FR-3.4.

Before writing, checks Hermes' own memory ledger for past scripts and
logged performance on similar products/angles, and nudges the prompt
toward whatever worked before (design doc 3.2, FR-3.4).
"""
import json

from agents.memory import search_similar_performance
from app.models import ResearchDossier
from agents.providers.gemini_client import run_task


SCRIPT_PROMPT_TEMPLATE = """\
Write 3 TikTok Shop script angles in Bahasa Malaysia for this product,
based only on the research below. Angles: Problem Hook, Tech Spec,
Aesthetic/Lifestyle. Each needs hook, body, cta, caption, hashtags,
and plain-language visual_notes (what to film, in what order).

What it does: {what_it_does}
Key benefits: {key_benefits}
USPs (each angle below should lean on a DIFFERENT one of these - don't
just restate the same USP three times):
{usps}
Positive reviews say: {review_summary_positive}
Negative reviews say: {review_summary_negative}

Ingredient/science research (use this for credibility where relevant -
keep claims hedged, e.g. "may support...", not definitive medical claims):
{ingredients_research}

Past-performance notes (favor these angles/hooks when relevant):
{memory_notes}

Return a JSON list of 3 objects, each with keys:
angle_type, hook_ms, body_ms, cta_ms, caption_ms, hashtags (list), visual_notes.
"""


def _format_usps(dossier: ResearchDossier) -> str:
    """usps is stored as a JSON-encoded list of 3 strings - render as a
    simple bullet list for the prompt."""
    return "\n".join(f"- {usp}" for usp in json.loads(dossier.usps))


def _format_ingredients_research(dossier: ResearchDossier) -> str:
    topics = json.loads(dossier.ingredients_research or "[]")
    if not topics:
        return "No ingredient/science research for this product."
    return "\n\n".join(
        f"{t['topic']}: {t['what_it_is']} {t['how_it_works']} Best for: {t['who_benefits']}"
        for t in topics
    )


def generate_scripts(dossier: ResearchDossier) -> list[dict]:
    """Calls Hermes to write 3 script variations for one approved dossier."""

    memory_notes = search_similar_performance(dossier) or "No relevant past data yet."

    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        what_it_does=dossier.what_it_does,
        key_benefits=dossier.key_benefits,
        usps=_format_usps(dossier),
        review_summary_positive=dossier.review_summary_positive,
        review_summary_negative=dossier.review_summary_negative,
        ingredients_research=_format_ingredients_research(dossier),
        memory_notes=memory_notes,
    )
    return run_task(prompt, expects_json=True)