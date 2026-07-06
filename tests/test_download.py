"""Tests for HTTP download helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from federalspendai.data.download import download_file
from federalspendai.http_client import DEFAULT_USER_AGENT


def test_download_file_sends_user_agent(tmp_path: Path):
    captured: dict = {}

    def fake_stream(method, url, **kwargs):
        captured["headers"] = kwargs.get("headers", {})
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.iter_bytes.return_value = [b"csv,data\n1,2\n"]
        return MagicMock(__enter__=lambda *_: response, __exit__=lambda *_: None)

    dest = tmp_path / "awards.csv"
    with patch("federalspendai.data.download.httpx.stream", side_effect=fake_stream):
        checksum = download_file("https://example.com/awards.csv", dest)

    assert dest.exists()
    assert checksum
    assert captured["headers"].get("User-Agent") == DEFAULT_USER_AGENT

