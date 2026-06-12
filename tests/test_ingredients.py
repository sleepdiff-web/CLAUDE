"""Tests for ingredient recognition / extraction (no network)."""
from trend_scout.ingredients import (
    candidate_from_query,
    core_ingredient,
    extract_candidates_from_text,
    is_known_ingredient,
    normalize,
)


def test_normalize():
    assert normalize("  Lion's Mane!! ") == "lion s mane"
    assert normalize("CoQ10") == "coq10"


def test_known_ingredient():
    assert is_known_ingredient("Ashwagandha")
    assert is_known_ingredient("organic ashwagandha root")  # sub-phrase match
    assert not is_known_ingredient("blue widget")


def test_core_ingredient_strips_modifiers():
    assert core_ingredient("berberine benefits for weight loss reddit") == "berberine"
    assert core_ingredient("best ashwagandha supplement dosage") == "ashwagandha"


def test_core_ingredient_prefers_most_specific():
    # Should keep the two-word form, not collapse to "magnesium".
    assert core_ingredient("magnesium glycinate reviews") == "magnesium glycinate"


def test_core_ingredient_novel_botanical():
    # Not in lexicon but ingredient-shaped -> surfaced as a NEW candidate.
    # "extract" is a modifier and is stripped, leaving the core novel term.
    assert core_ingredient("kanna extract") == "kanna"
    # A botanical-suffix novel term is kept whole.
    assert core_ingredient("muira puama bark") == "muira puama bark"


def test_core_ingredient_rejects_pure_junk():
    assert core_ingredient("best supplement reddit") is None
    assert core_ingredient("how to take vitamins daily") is None


def test_candidate_from_query():
    c = candidate_from_query("berberine dosage", source="trends")
    assert c is not None
    assert c.term == "berberine"
    assert c.known is True
    assert c.source == "trends"


def test_extract_from_text_finds_known():
    text = "Has anyone tried tongkat ali and fadogia for testosterone?"
    terms = {c.term for c in extract_candidates_from_text(text, "reddit")}
    assert "tongkat ali" in terms
