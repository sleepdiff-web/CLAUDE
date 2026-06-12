"""Deep links from an ingredient term into research tools.

The Kalodata link is best-effort: it points their product search at the
ingredient keyword so you can jump straight from a trending ingredient to the
supplements selling on TikTok Shop. Adjust the template in config.yaml if
Kalodata changes their URL scheme.
"""
from __future__ import annotations

from urllib.parse import quote_plus

_DEFAULT_KALODATA = "https://www.kalodata.com/product?keyword={query}"


def kalodata_url(term: str, template: str = _DEFAULT_KALODATA) -> str:
    return template.format(query=quote_plus(term))


def google_trends_url(term: str, geo: str = "") -> str:
    base = f"https://trends.google.com/trends/explore?q={quote_plus(term)}"
    if geo:
        base += f"&geo={geo}"
    return base
