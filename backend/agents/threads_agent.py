"""Threads post-copy agent — the text-post analogue of agents/script_agent.py.
A Threads post is one short block (<=500 chars), not a multi-shot video
script, so the shape is simpler on purpose."""
from app.models import ResearchDossier

THREADS_PROMPT_TEMPLATE = """\
Write 3 short Threads post variations in Bahasa Malaysia promoting this
product as a Shopee affiliate. Each under 400 characters (room for the
link), ending with a natural CTA, plus 2-3 relevant hashtags. Don't
invent claims outside the research below.

What it does: {what_it_does}
Key benefits: {key_benefits}
USP: {usp}
Positive reviews say: {review_summary_positive}

Return a JSON list of 3 strings — post text only, WITHOUT the link
(it's appended separately so it stays a trackable/clickable link).
"""


def generate_threads_posts(dossier: ResearchDossier) -> list[str]:
    from agents.hermes_client import run_task

    prompt = THREADS_PROMPT_TEMPLATE.format(
        what_it_does=dossier.what_it_does,
        key_benefits=dossier.key_benefits,
        usp=dossier.usp,
        review_summary_positive=dossier.review_summary_positive,
    )
    return run_task(prompt, expects_json=True)