from datetime import date

from dtc_scout.models import BrandMetrics
from dtc_scout.vetting import Criteria, brand_age_ok, evaluate

TODAY = date(2026, 7, 9)
CRITERIA = Criteria(
    min_active_ads=12,
    min_new_ads_30d=4,
    max_brand_age_months=12,
    require_shopify=True,
    big_brand_rank_cutoff=5000,
    exclude_domains=("amazon.com",),
)


def good_brand(**overrides) -> BrandMetrics:
    base = dict(
        page_id="1", page_name="GlowCo", domain="glowco.com", niche="skincare",
        active_ads=30, total_ads=80, new_ads_30d=10, first_ad_date="2026-01-15",
        total_eu_reach=500_000, is_shopify=True, is_subscription=True,
        traffic_rank=90_000, traffic_tier="medium",
    )
    base.update(overrides)
    return BrandMetrics(**base)


def test_scaling_new_shopify_brand_passes():
    assert evaluate(good_brand(), CRITERIA, TODAY).passed


def test_too_few_active_ads_fails():
    result = evaluate(good_brand(active_ads=5), CRITERIA, TODAY)
    assert not result.passed and "active ads 5" in result.reasons[0]


def test_stopped_launching_creatives_fails():
    assert not evaluate(good_brand(new_ads_30d=1), CRITERIA, TODAY).passed


def test_old_brand_fails():
    result = evaluate(good_brand(first_ad_date="2023-01-01"), CRITERIA, TODAY)
    assert not result.passed and "older than 12 months" in result.reasons[0]


def test_household_name_traffic_rank_fails():
    # A calvinklein.com-class domain: huge Tranco rank
    result = evaluate(good_brand(traffic_rank=800), CRITERIA, TODAY)
    assert not result.passed and "household-name" in result.reasons[0]


def test_non_shopify_fails_but_unreachable_store_passes():
    assert not evaluate(good_brand(is_shopify=False), CRITERIA, TODAY).passed
    # None = couldn't check; benefit of the doubt
    assert evaluate(good_brand(is_shopify=None), CRITERIA, TODAY).passed


def test_excluded_domain_fails():
    assert not evaluate(good_brand(domain="amazon.com"), CRITERIA, TODAY).passed


def test_missing_domain_fails():
    assert not evaluate(good_brand(domain=""), CRITERIA, TODAY).passed


def test_all_failures_are_reported_together():
    result = evaluate(good_brand(active_ads=0, new_ads_30d=0, is_shopify=False), CRITERIA, TODAY)
    assert len(result.reasons) == 3


def test_brand_age_edge_cases():
    assert brand_age_ok("", TODAY, 12)            # unknown date passes
    assert brand_age_ok("not-a-date", TODAY, 12)  # unparseable passes
    assert brand_age_ok("2025-08-01", TODAY, 12)
    assert not brand_age_ok("2024-01-01", TODAY, 12)
