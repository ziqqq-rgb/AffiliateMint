"""
Script writing agent - FR-3.1 - FR-3.4.

Before writing, checks Hermes' own memory ledger for past scripts and
logged performance on similar products/angles, and nudges the prompt
toward whatever worked before (design doc 3.2, FR-3.4).
"""
from agents.dossier_format import format_deep_research, format_usps
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

Deep research (material tech, brand/model heritage, certifications, or
ingredients - whichever applies to this product): use this as a
credibility booster woven INTO a hook or USP where it genuinely
strengthens the pitch (e.g. "since 1966" for a heritage sneaker, or
"IP68-rated" for electronics) - don't force it into every angle if it
only naturally fits one:
{deep_research}

Past-performance notes (favor these angles/hooks when relevant):
{memory_notes}

Return a JSON list of 3 objects, each with keys:
angle_type, hook_ms, body_ms, cta_ms, caption_ms, hashtags (list), visual_notes.
"""


def generate_scripts(dossier: ResearchDossier) -> list[dict]:
    """Calls Hermes to write 3 script variations for one approved dossier."""

    memory_notes = search_similar_performance(dossier) or "No relevant past data yet."

    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        what_it_does=dossier.what_it_does,
        key_benefits=dossier.key_benefits,
        usps=format_usps(dossier),
        review_summary_positive=dossier.review_summary_positive,
        review_summary_negative=dossier.review_summary_negative,
        deep_research=format_deep_research(dossier),
        memory_notes=memory_notes,
    )
    return run_task(prompt, expects_json=True)