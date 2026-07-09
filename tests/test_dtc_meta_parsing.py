from datetime import date

from dtc_scout.models import Ad
from dtc_scout.pipeline import build_metrics
from dtc_scout.sources.meta_ad_library import extract_domain, parse_ad


def test_extract_domain_shapes():
    assert extract_domain("EXAMPLE.COM") == "example.com"
    assert extract_domain("www.glowco.com | Free shipping") == "glowco.com"
    assert extract_domain("https://shop.glowco.com/pages/quiz?x=1") == "shop.glowco.com"
    assert extract_domain("") == ""
    assert extract_domain("50% off today only!") == ""


def test_extract_domain_filters_non_store_hosts():
    assert extract_domain("fb.me") == ""
    assert extract_domain("linktr.ee") == ""
    assert extract_domain("apps.apple.com") == ""


def test_parse_ad_normalises_raw_record():
    raw = {
        "id": "123",
        "page_id": "42",
        "page_name": "GlowCo",
        "ad_creative_bodies": ["Tired of dull skin?"],
        "ad_creative_link_titles": ["Get 20% off"],
        "ad_creative_link_captions": ["glowco.com"],
        "ad_delivery_start_time": "2026-06-01T07:00:00+0000",
        "eu_total_reach": "15000",
        "publisher_platforms": ["facebook", "instagram"],
    }
    ad = parse_ad(raw, niche="skincare")
    assert ad.archive_id == "123"
    assert ad.start_date == "2026-06-01"
    assert ad.active  # no stop time -> still delivering
    assert ad.eu_reach == 15000
    assert ad.platforms == "facebook,instagram"
    assert ad.niche == "skincare"


def _ad(archive_id, start, stop="", reach=0, caption="glowco.com"):
    return Ad(archive_id=archive_id, page_id="42", page_name="GlowCo",
              start_date=start, stop_date=stop, eu_reach=reach, link_caption=caption)


def test_build_metrics_aggregates_signals():
    today = date(2026, 7, 9)
    ads = [
        _ad("1", "2026-01-10", reach=1000),                    # old, active
        _ad("2", "2026-06-20", reach=2000),                    # new (30d), active
        _ad("3", "2026-06-25", stop="2026-07-01", reach=500),  # new but stopped
        _ad("4", "2026-07-01", reach=300, caption="other.com"),
    ]
    m = build_metrics("42", "GlowCo", ads, today, "skincare")
    assert m.active_ads == 3
    assert m.total_ads == 4
    assert m.new_ads_30d == 3
    assert m.first_ad_date == "2026-01-10"
    assert m.total_eu_reach == 3800
    assert m.domain == "glowco.com"  # majority vote across ad links
