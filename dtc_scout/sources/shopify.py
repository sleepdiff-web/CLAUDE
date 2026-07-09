"""Shopify storefront signals: platform detection, subscription apps, products.

All free: `/products.json` is public on most Shopify stores, and subscription
apps leave recognisable script/domain fingerprints in the storefront HTML.
"""
from __future__ import annotations

import logging
import re

import requests

log = logging.getLogger(__name__)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Fingerprints of the major Shopify subscription apps. Any hit on the
# storefront HTML => the brand sells subscriptions (the "subs vs one-time"
# filter from the spec).
SUBSCRIPTION_MARKERS = [
    r"rechargepayments\.com",
    r"static\.rechargecdn\.com",
    r"skio\.com|skiocdn",
    r"stay\.ai",
    r"loopsubscriptions|loopwork",
    r"smartrr\.com",
    r"ordergroove",
    r"appstle",
    r"seal-subscriptions",
    r"bold.*subscriptions|boldapps\.net/recurring",
    r"selling_plan",  # native Shopify subscriptions in product JSON/HTML
]
_SUB_RE = re.compile("|".join(SUBSCRIPTION_MARKERS), re.IGNORECASE)

_SHOPIFY_HTML_RE = re.compile(r"cdn\.shopify\.com|Shopify\.theme|shopify-features", re.IGNORECASE)


def detect_subscription(html: str) -> bool:
    """Pure check for subscription-app fingerprints in storefront HTML."""
    return bool(html and _SUB_RE.search(html))


def looks_like_shopify(html: str) -> bool:
    """Pure check for Shopify fingerprints in storefront HTML."""
    return bool(html and _SHOPIFY_HTML_RE.search(html))


class ShopifyProbe:
    """Network-facing probe for one storefront domain."""

    def __init__(self, session: requests.Session | None = None, timeout: int = 15) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_homepage(self, domain: str) -> str:
        try:
            resp = self.session.get(f"https://{domain}/", headers=UA, timeout=self.timeout)
            return resp.text if resp.ok else ""
        except requests.RequestException as exc:
            log.debug("homepage fetch failed for %s: %s", domain, exc)
            return ""

    def fetch_products(self, domain: str, limit: int = 250) -> list[dict]:
        """Public product catalogue; also doubles as a Shopify detector."""
        try:
            resp = self.session.get(
                f"https://{domain}/products.json",
                params={"limit": limit},
                headers=UA,
                timeout=self.timeout,
            )
            if resp.ok and "application/json" in resp.headers.get("content-type", ""):
                return resp.json().get("products", []) or []
        except (requests.RequestException, ValueError) as exc:
            log.debug("products.json failed for %s: %s", domain, exc)
        return []

    def probe(self, domain: str) -> dict:
        """Returns {'is_shopify': bool|None, 'is_subscription': bool|None,
        'product_count': int}. None means the store was unreachable."""
        html = self.fetch_homepage(domain)
        products = self.fetch_products(domain)
        if not html and not products:
            return {"is_shopify": None, "is_subscription": None, "product_count": 0}
        is_shopify = bool(products) or looks_like_shopify(html)
        return {
            "is_shopify": is_shopify,
            "is_subscription": detect_subscription(html),
            "product_count": len(products),
        }
