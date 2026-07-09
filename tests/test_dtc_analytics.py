from datetime import date

from dtc_scout.analytics import avg_ad_life_days, catalog_freshness, median_price, mix
from dtc_scout.sources.shopify import parse_products

TODAY = date(2026, 7, 9)


def test_median_price():
    prods = [{"price": 20.0}, {"price": 45.0}, {"price": 30.0}, {"price": None}]
    assert median_price(prods) == 30.0
    assert median_price([]) is None
    assert median_price([{"price": None}]) is None


def test_avg_ad_life_mixes_stopped_and_active():
    ads = [
        {"start_date": "2026-06-01", "stop_date": "2026-06-11"},  # 10 days
        {"start_date": "2026-06-29", "stop_date": ""},            # 10 days so far
        {"start_date": "", "stop_date": ""},                      # ignored
    ]
    assert avg_ad_life_days(ads, TODAY) == 10
    assert avg_ad_life_days([], TODAY) is None


def test_catalog_freshness():
    prods = [{"created_at": "2026-05-14"}, {"created_at": "2026-06-30"}, {"created_at": ""}]
    f = catalog_freshness(prods)
    assert f == {"newest": "2026-06-30", "oldest": "2026-05-14", "span_days": 47}
    assert catalog_freshness([])["newest"] is None


def test_mix_excludes_unlabeled():
    ads = [
        {"awareness_level": "unaware"}, {"awareness_level": "unaware"},
        {"awareness_level": "problem_aware"}, {"awareness_level": "unknown"},
    ]
    rows = mix(ads, "awareness_level")
    assert rows[0] == {"label": "unaware", "count": 2, "pct": 67}
    assert rows[1]["label"] == "problem_aware"


def test_parse_products_normalises_shopify_json():
    raw = [{
        "handle": "glow-serum",
        "title": "Glow Serum",
        "variants": [{"price": "39.00"}, {"price": "29.00"}, {"price": "bad"}],
        "images": [{"src": "https://cdn.shopify.com/x.jpg"}],
        "created_at": "2026-05-14T10:00:00-04:00",
    }, {
        "handle": "empty", "title": "No variants",
    }]
    out = parse_products(raw)
    assert out[0] == {"handle": "glow-serum", "title": "Glow Serum", "price": 29.0,
                      "image": "https://cdn.shopify.com/x.jpg", "created_at": "2026-05-14"}
    assert out[1]["price"] is None and out[1]["image"] == ""
