"""Taxonomies + prompt construction for creative classification."""
from __future__ import annotations

# Eugene Schwartz awareness stages — the filter the spec leans on hardest.
AWARENESS_LEVELS = ["unaware", "problem_aware", "solution_aware", "product_aware", "most_aware"]

# v1 classifies from ad COPY only (no vision pass yet), so visual treatment is
# inferred only when the copy/format makes it evident; else "unknown".
VISUAL_TREATMENTS = [
    "ugc", "talking_head", "product_demo", "ai_animation", "static_image",
    "text_only", "unknown",
]

AUTHORITY_FIGURES = [
    "doctor", "dermatologist", "nutritionist", "scientist", "founder",
    "celebrity", "none", "unknown",
]

OFFER_TYPES = ["subscription", "one_time", "unknown"]

SYSTEM = (
    "You classify direct-response e-commerce ad creatives for a media buyer's "
    "research database. Answer with strict JSON only — no prose."
)


def build_batch_prompt(ads: list[dict]) -> str:
    """One prompt classifying a batch of ads; expects a JSON array back."""
    lines = [
        "Classify each ad below on four dimensions. Definitions:",
        f"- awareness_level (Eugene Schwartz): one of {AWARENESS_LEVELS}.",
        "  unaware = hooks on a story/curiosity with no problem named;",
        "  problem_aware = agitates a problem, no solution category named;",
        "  solution_aware = names the solution category, not the product;",
        "  product_aware = product-led, differentiating vs alternatives;",
        "  most_aware = offer/discount/urgency to people who already know the product.",
        f"- visual_treatment: one of {VISUAL_TREATMENTS}; use 'unknown' unless the copy makes it evident.",
        f"- authority_figure: one of {AUTHORITY_FIGURES} — a credibility figure cited or featured.",
        f"- offer_type: one of {OFFER_TYPES} — does the copy sell a subscription or a one-time purchase?",
        "",
        'Return a JSON array, one object per ad, in the same order: '
        '[{"id": "...", "awareness_level": "...", "visual_treatment": "...", '
        '"authority_figure": "...", "offer_type": "..."}]',
        "",
        "Ads:",
    ]
    for ad in ads:
        lines.append(
            f'--- id: {ad["archive_id"]}\n'
            f'headline: {ad.get("link_title", "")}\n'
            f'body: {ad.get("body", "")[:1200]}'
        )
    return "\n".join(lines)
