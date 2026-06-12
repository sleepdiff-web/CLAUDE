"""Thin wrapper around pytrends with batching and backoff.

pytrends is an unofficial scraper of Google Trends. It is free but rate
limited (HTTP 429) and occasionally flaky, so every call goes through retry
with exponential backoff. pytrends is imported lazily so the rest of the
package (and the tests) work without it installed.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

log = logging.getLogger("trend_scout.trends")


class TrendsClient:
    def __init__(
        self,
        geo: str = "",
        timeframe: str = "today 3-m",
        *,
        hl: str = "en-US",
        max_retries: int = 4,
        base_sleep: float = 3.0,
        request_pause: float = 1.5,
        proxies: list[str] | None = None,
    ) -> None:
        self.geo = geo
        self.timeframe = timeframe
        self.hl = hl
        self.max_retries = max_retries
        self.base_sleep = base_sleep
        self.request_pause = request_pause
        # Google Trends blocks datacenter IPs (incl. CI runners) with HTTP 403.
        # Supply residential/rotating proxies to run from the cloud. Falls back
        # to the TRENDS_PROXIES env var (comma-separated) if not passed.
        if proxies is None:
            env = os.environ.get("TRENDS_PROXIES", "")
            proxies = [p.strip() for p in env.split(",") if p.strip()]
        self.proxies = proxies
        self._pt = None  # lazily constructed TrendReq

    def _client(self):
        if self._pt is None:
            from pytrends.request import TrendReq  # lazy import

            # retries/backoff_factor here cover transport-level hiccups; our
            # own _with_backoff covers 429s from the Trends front end.
            kwargs: dict[str, Any] = dict(hl=self.hl, tz=0, retries=2, backoff_factor=0.5)
            if self.proxies:
                kwargs["proxies"] = self.proxies
                log.info("Trends using %d proxy endpoint(s)", len(self.proxies))
            self._pt = TrendReq(**kwargs)
        return self._pt

    def _with_backoff(self, fn, *args, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # pytrends raises generic + ResponseError
                last_exc = exc
                wait = self.base_sleep * (2 ** attempt)
                msg = str(exc)
                if "429" in msg or "rate" in msg.lower():
                    wait *= 2  # be extra gentle on explicit rate limits
                log.warning(
                    "Trends call failed (attempt %d/%d): %s — sleeping %.1fs",
                    attempt + 1, self.max_retries, msg, wait,
                )
                time.sleep(wait)
        assert last_exc is not None
        raise last_exc

    # -- public API -------------------------------------------------------
    def rising_related_queries(self, seed: str) -> list[str]:
        """Return the 'rising'/'top' related query strings for a seed term."""
        pt = self._client()

        def _call() -> list[str]:
            pt.build_payload([seed], timeframe=self.timeframe, geo=self.geo)
            data: dict[str, Any] = pt.related_queries()
            block = data.get(seed) or {}
            out: list[str] = []
            for key in ("rising", "top"):
                df = block.get(key)
                if df is not None and not df.empty and "query" in df:
                    out.extend(str(q) for q in df["query"].tolist())
            return out

        try:
            result = self._with_backoff(_call)
        except Exception as exc:
            log.error("rising_related_queries(%r) gave up: %s", seed, exc)
            result = []
        time.sleep(self.request_pause)
        return result

    def interest_over_time(self, terms: list[str]) -> dict[str, list[float]]:
        """Map each term -> oldest-first list of interest values (0-100).

        pytrends accepts up to 5 terms per payload; batch accordingly.
        Terms with no data are returned as an empty list.
        """
        pt = self._client()
        out: dict[str, list[float]] = {t: [] for t in terms}

        for batch in _chunks(terms, 5):
            def _call(batch=batch):
                pt.build_payload(batch, timeframe=self.timeframe, geo=self.geo)
                return pt.interest_over_time()

            try:
                df = self._with_backoff(_call)
            except Exception as exc:
                log.error("interest_over_time(%r) gave up: %s", batch, exc)
                continue

            if df is None or df.empty:
                continue
            for term in batch:
                if term in df.columns:
                    out[term] = [float(v) for v in df[term].tolist()]
            time.sleep(self.request_pause)

        return out


def _chunks(seq: list[str], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]
