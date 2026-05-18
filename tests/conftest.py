"""
Shared pytest fixtures for weather-skill tests.

Provides:
- mock_http: Patches urllib.request.urlopen to replay canned API responses
  from fixtures/api-responses/{provider}/manifest.json.
- frozen_clock: Freezes time to 2026-01-01T00:00:00+00:00 for deterministic output.
"""

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from freezegun import freeze_time

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "api-responses"
FROZEN_TIME = "2026-01-01T00:00:00+00:00"

_PROVIDERS = ("hko", "jma", "sg_nea", "us_nws", "openweathermap")


def _load_manifests() -> dict[str, dict[str, bytes]]:
    """Load all provider manifests and their response bodies.

    Returns {url: response_bytes} for every URL across all manifests.
    """
    url_map: dict[str, bytes] = {}
    for provider in _PROVIDERS:
        manifest_path = FIXTURES_ROOT / provider / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for url, rel_path in manifest.get("urls", {}).items():
            # OWM uses <API_KEY> placeholder — normalize to a matchable URL
            normalized = url.replace("<API_KEY>", "test-key")
            body_path = FIXTURES_ROOT / provider / rel_path
            if body_path.exists():
                url_map[normalized] = body_path.read_bytes()
    return url_map


class _FakeResponse:
    """Minimal file-like object that mimics urllib.request.urlopen return value."""

    def __init__(self, body: bytes):
        self._body = BytesIO(body)
        self.status = 200
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


@pytest.fixture()
def mock_http():
    """Patch urllib.request.urlopen to return fixture-backed responses."""
    url_map = _load_manifests()

    def _urlopen(request, timeout=10):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        # Normalize OWM placeholder URLs
        url = url.replace("<API_KEY>", "test-key")
        if url in url_map:
            return _FakeResponse(url_map[url])
        raise FileNotFoundError(f"No fixture for URL: {url}")

    with patch("urllib.request.urlopen", _urlopen):
        yield


@pytest.fixture()
def frozen_clock():
    """Freeze time to 2026-01-01T00:00:00+00:00."""
    with freeze_time(FROZEN_TIME):
        yield
