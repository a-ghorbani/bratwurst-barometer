"""Small, dependency-free download helpers with local caching."""

from __future__ import annotations

import urllib.request
from pathlib import Path


USER_AGENT = "germany-temperature-analysis/0.1"


def download_text(url: str, timeout_seconds: int = 60) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def download_file(url: str, path: Path, timeout_seconds: int = 120) -> None:
    """Download a URL to `path` unless a non-empty cached file already exists."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return

    tmp_path = path.with_suffix(path.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        tmp_path.write_bytes(response.read())
    tmp_path.replace(path)
