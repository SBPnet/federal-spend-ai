"""HTTP download helpers with checksum tracking."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from federalspendai.config import Settings, get_settings


def file_checksum(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def download_file(url: str, dest: Path, settings: Settings | None = None) -> str:
  """Download a URL to dest; return SHA-256 checksum."""
  settings = settings or get_settings()
  dest.parent.mkdir(parents=True, exist_ok=True)
  digest = hashlib.sha256()
  with httpx.stream("GET", url, timeout=settings.request_timeout, follow_redirects=True) as response:
    response.raise_for_status()
    with dest.open("wb") as handle:
      for chunk in response.iter_bytes():
        digest.update(chunk)
        handle.write(chunk)
  return digest.hexdigest()
