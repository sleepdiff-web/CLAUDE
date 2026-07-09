"""Creative classifier: Claude API when ANTHROPIC_API_KEY is set, keyword
heuristics otherwise — the pipeline always runs end-to-end for free."""
from __future__ import annotations

import json
import logging
import os
import re

from .prompts import (
    AUTHORITY_FIGURES,
    AWARENESS_LEVELS,
    OFFER_TYPES,
    SYSTEM,
    VISUAL_TREATMENTS,
    build_batch_prompt,
)

log = logging.getLogger(__name__)

_VALID = {
    "awareness_level": set(AWARENESS_LEVELS) | {"unknown"},
    "visual_treatment": set(VISUAL_TREATMENTS),
    "authority_figure": set(AUTHORITY_FIGURES),
    "offer_type": set(OFFER_TYPES),
}


def parse_classification_response(text: str) -> list[dict]:
    """Extract and sanity-check the JSON array from a model response."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            continue
        clean = {"id": str(item["id"])}
        for key, valid in _VALID.items():
            value = str(item.get(key, "unknown")).strip().lower()
            clean[key] = value if value in valid else "unknown"
        out.append(clean)
    return out


# --- free keyword fallback ----------------------------------------------------

_RULES = {
    "offer_type": [
        ("subscription", r"subscri|monthly (?:delivery|supply)|cancel anytime|refill"),
        ("one_time", r"one[- ]time|buy once"),
    ],
    "authority_figure": [
        ("dermatologist", r"dermatologist"),
        ("doctor", r"\bdr\.|\bdoctor|physician|md[- ]approved"),
        ("nutritionist", r"nutritionist|dietitian"),
        ("scientist", r"scientist|clinically (?:proven|tested)|lab[- ]tested"),
        ("founder", r"\bi founded|\bour founder|as a founder"),
    ],
    "awareness_level": [
        ("most_aware", r"\b\d{1,2}% off|sale ends|last chance|use code|black friday"),
        ("product_aware", r"unlike other|vs\.? (?:the )?(?:other|leading)|why \w+ beats"),
        ("problem_aware", r"struggl|tired of|sick of|can't seem to|frustrat"),
    ],
}


def classify_by_keywords(ads: list[dict]) -> list[dict]:
    """Zero-cost heuristic pass. Deliberately conservative: 'unknown' > wrong."""
    results = []
    for ad in ads:
        text = f"{ad.get('link_title', '')} {ad.get('body', '')}".lower()
        result = {"id": ad["archive_id"], "visual_treatment": "unknown"}
        for field, rules in _RULES.items():
            result[field] = "unknown"
            for label, pattern in rules:
                if re.search(pattern, text):
                    result[field] = label
                    break
        if result["authority_figure"] == "unknown":
            result["authority_figure"] = "none" if text.strip() else "unknown"
        results.append(result)
    return results


def classify_with_claude(ads: list[dict], model: str, batch_size: int = 8) -> list[dict]:
    import anthropic  # imported lazily so the dependency stays optional

    client = anthropic.Anthropic()
    results: list[dict] = []
    for i in range(0, len(ads), batch_size):
        batch = ads[i : i + batch_size]
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=1500,
                system=SYSTEM,
                messages=[{"role": "user", "content": build_batch_prompt(batch)}],
            )
            results.extend(parse_classification_response(resp.content[0].text))
        except Exception as exc:  # API errors shouldn't kill the whole run
            log.warning("classification batch failed (%s); falling back to keywords", exc)
            results.extend(classify_by_keywords(batch))
    return results


def classify_ads(ads: list[dict], model: str, batch_size: int = 8) -> dict[str, dict]:
    """Classify ad dicts; returns {archive_id: classification}."""
    if not ads:
        return {}
    if os.environ.get("ANTHROPIC_API_KEY"):
        results = classify_with_claude(ads, model, batch_size)
    else:
        log.info("ANTHROPIC_API_KEY not set — using free keyword classifier")
        results = classify_by_keywords(ads)
    return {r["id"]: r for r in results}
