from dtc_scout.classify.classifier import classify_by_keywords, parse_classification_response
from dtc_scout.classify.prompts import build_batch_prompt


def test_parse_valid_response_with_prose_wrapper():
    text = 'Here you go:\n[{"id": "1", "awareness_level": "unaware", '
    text += '"visual_treatment": "ugc", "authority_figure": "none", "offer_type": "one_time"}]'
    results = parse_classification_response(text)
    assert results == [{
        "id": "1", "awareness_level": "unaware", "visual_treatment": "ugc",
        "authority_figure": "none", "offer_type": "one_time",
    }]


def test_parse_sanitises_invalid_labels():
    text = '[{"id": "1", "awareness_level": "SUPER aware", "offer_type": "Subscription"}]'
    result = parse_classification_response(text)[0]
    assert result["awareness_level"] == "unknown"   # not in taxonomy
    assert result["offer_type"] == "subscription"   # case-normalised
    assert result["visual_treatment"] == "unknown"  # missing -> unknown


def test_parse_garbage_returns_empty():
    assert parse_classification_response("no json here") == []
    assert parse_classification_response("[{broken json]") == []


def test_keyword_fallback_is_conservative():
    ads = [
        {"archive_id": "1", "link_title": "Subscribe & save 20%",
         "body": "Cancel anytime. Dermatologist approved."},
        {"archive_id": "2", "link_title": "", "body": "A story about my morning."},
    ]
    results = {r["id"]: r for r in classify_by_keywords(ads)}
    assert results["1"]["offer_type"] == "subscription"
    assert results["1"]["authority_figure"] == "dermatologist"
    assert results["2"]["offer_type"] == "unknown"        # no signal -> unknown, not a guess
    assert results["2"]["authority_figure"] == "none"


def test_batch_prompt_contains_ads_and_taxonomy():
    prompt = build_batch_prompt([{"archive_id": "9", "link_title": "T", "body": "B"}])
    assert "id: 9" in prompt
    assert "unaware" in prompt and "most_aware" in prompt
    assert "JSON array" in prompt
