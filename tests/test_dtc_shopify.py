from dtc_scout.sources.shopify import detect_subscription, looks_like_shopify
from dtc_scout.sources.traffic import rank_to_tier


def test_detects_shopify_fingerprints():
    assert looks_like_shopify('<script src="https://cdn.shopify.com/s/x.js"></script>')
    assert looks_like_shopify("<script>Shopify.theme = {id: 1};</script>")
    assert not looks_like_shopify("<html><body>wordpress site</body></html>")
    assert not looks_like_shopify("")


def test_detects_subscription_apps():
    assert detect_subscription('<script src="https://static.rechargecdn.com/x.js">')
    assert detect_subscription('<div data-skio.com-widget>')
    assert detect_subscription('{"selling_plan": 123}')  # native Shopify subs
    assert not detect_subscription("<html>one time purchase only</html>")
    assert not detect_subscription("")


def test_rank_to_tier_buckets():
    assert rank_to_tier(None, 60000, 250000) == "unknown"
    assert rank_to_tier(50000, 60000, 250000) == "high"
    assert rank_to_tier(100000, 60000, 250000) == "medium"
    assert rank_to_tier(900000, 60000, 250000) == "low"
