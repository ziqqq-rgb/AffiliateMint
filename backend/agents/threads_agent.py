"""Threads post-copy agent — the text-post analogue of agents/script_agent.py.
A Threads post is one short block (<=500 chars), not a multi-shot video
script, so the shape is simpler on purpose."""
from agents.dossier_format import format_deep_research, format_usps
from app.models import ResearchDossier
from agents.memory import search_similar_threads_posts
from agents.providers.gemini_client import run_task

THREADS_PROMPT_TEMPLATE = """\
Write 3 short Threads post variations in Bahasa Malaysia promoting this
product as a Shopee affiliate. Each under 400 characters (room for the
link), ending with a natural CTA, plus 2-3 relevant hashtags. Don't
invent claims outside the research below.

What it does: {what_it_does}
Key benefits: {key_benefits}
USPs (each post should lean on a DIFFERENT one of these):
{usps}
Positive reviews say: {review_summary_positive}

Deep research (material tech, brand/model heritage, certifications, or
ingredients - whichever applies to this product): weave in as a
credibility detail in ONE of the 3 posts where it genuinely strengthens
the pitch - skip it in the other two rather than repeating it three times:
{deep_research}

Past posts the operator kept/edited (favor similar phrasing when relevant):
{memory_notes}

Return a JSON list of 3 strings — post text only, WITHOUT the link
(it's appended separately so it stays a trackable/clickable link).
"""


def generate_threads_posts(dossier: ResearchDossier) -> list[str]:
    memory_notes = search_similar_threads_posts(dossier) or "No relevant past data yet."
    prompt = THREADS_PROMPT_TEMPLATE.format(
        what_it_does=dossier.what_it_does,
        key_benefits=dossier.key_benefits,
        usps=format_usps(dossier),
        review_summary_positive=dossier.review_summary_positive,
        deep_research=format_deep_research(dossier),
        memory_notes=memory_notes,
    )
    return run_task(prompt, expects_json=True)