"""Download ad creatives (video/image) from Meta ad snapshot pages.

The ads_archive API returns an authenticated `ad_snapshot_url` per ad. That
page embeds the creative's CDN URLs in inline JSON (`video_hd_url`,
`original_image_url`, ...). We parse those out and save the media next to the
dashboard (output/media/<archive_id>.mp4|.jpg) so cards can show and play the
real creative offline — and so "Download HD" is just a local file.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import requests

log = logging.getLogger(__name__)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Preference order: HD video, SD video, original image, resized image.
_PATTERNS = [
    ("video", re.compile(r'"video_hd_url"\s*:\s*"(https:[^"]+)"')),
    ("video", re.compile(r'"video_sd_url"\s*:\s*"(https:[^"]+)"')),
    ("image", re.compile(r'"original_image_url"\s*:\s*"(https:[^"]+)"')),
    ("image", re.compile(r'"resized_image_url"\s*:\s*"(https:[^"]+)"')),
]


def _unescape(url: str) -> str:
    """Snapshot pages JSON-escape URLs: https:\\/\\/... and \\u0025 etc."""
    url = url.replace("\\/", "/")
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), url)


def extract_media_url(html: str) -> tuple[str, str] | None:
    """Pure parse: returns (media_type, url) for the best creative, or None."""
    if not html:
        return None
    for media_type, pattern in _PATTERNS:
        match = pattern.search(html)
        if match:
            return media_type, _unescape(match.group(1))
    return None


class MediaFetcher:
    def __init__(self, out_dir: Path, session: requests.Session | None = None,
                 timeout: int = 30) -> None:
        self.dir = out_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch(self, archive_id: str, snapshot_url: str) -> tuple[str, str] | None:
        """Download one ad's creative. Returns (media_type, relative_path)
        or None. Already-downloaded files are reused, so re-runs are cheap."""
        for ext, mt in ((".mp4", "video"), (".jpg", "image")):
            existing = self.dir / f"{archive_id}{ext}"
            if existing.exists() and existing.stat().st_size > 0:
                return mt, f"{self.dir.name}/{existing.name}"
        if not snapshot_url:
            return None
        try:
            page = self.session.get(snapshot_url, headers=UA, timeout=self.timeout)
            found = extract_media_url(page.text if page.ok else "")
            if not found:
                return None
            media_type, url = found
            ext = ".mp4" if media_type == "video" else ".jpg"
            target = self.dir / f"{archive_id}{ext}"
            with self.session.get(url, headers=UA, timeout=self.timeout * 2, stream=True) as resp:
                if not resp.ok:
                    return None
                with target.open("wb") as fh:
                    for chunk in resp.iter_content(chunk_size=1 << 16):
                        fh.write(chunk)
            return media_type, f"{self.dir.name}/{target.name}"
        except requests.RequestException as exc:
            log.debug("media fetch failed for %s: %s", archive_id, exc)
            return None
