from __future__ import annotations

import os
from pathlib import Path

import pytest

from mobile_automation.config import Settings, get_settings
from mobile_automation.qr_assets import build_generated_qr_cases, ensure_qr_image


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_settings(tmp_path: Path, **overrides) -> Settings:
    qr_path = tmp_path / "generated_qr.png"
    env = {
        "QR_GENERATED_IMAGE_PATH": str(qr_path),
        "QR_AMOUNT": "100",
        "QR_INVOICE_ID": "12345",
        "QR_INVOICE_TITLE": "title",
        "QR_MEGAPOLIS_CONTRACT": "67890",
        "QR_COMMON_ENABLED": "true",
        "QR_MEGAPOLIS_ENABLED": "true",
        "CLIENT_BIN": "999999999999",
    }
    env.update(overrides)
    for key, value in env.items():
        os.environ[key] = value
    return Settings()


class TestEnsureQrImage:
    def test_returns_explicit_image_path(self, tmp_path):
        explicit = tmp_path / "explicit.png"
        explicit.write_bytes(b"fake")
        settings = _make_settings(tmp_path, QR_IMAGE_PATH=str(explicit))
        assert ensure_qr_image(settings) == str(explicit)

    def test_generates_image_from_source_url(self, tmp_path, monkeypatch):
        monkeypatch.delenv("QR_IMAGE_PATH", raising=False)
        settings = _make_settings(
            tmp_path,
            QR_SOURCE_URL="https://example.com/qr/data",
        )
        result = ensure_qr_image(settings)
        assert Path(result).is_file()
        assert Path(result).stat().st_size > 0

    def test_returns_empty_when_nothing_configured(self, tmp_path, monkeypatch):
        for key in ("QR_IMAGE_PATH", "QR_SOURCE_URL", "QR_SOURCE_PAYLOAD"):
            monkeypatch.delenv(key, raising=False)
        settings = _make_settings(tmp_path)
        assert ensure_qr_image(settings) == ""


class TestBuildGeneratedQrCases:
    def test_no_client_bin_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLIENT_BIN", raising=False)
        settings = _make_settings(tmp_path)
        # _make_settings sets CLIENT_BIN; override
        os.environ.pop("CLIENT_BIN", None)
        settings = Settings()
        assert build_generated_qr_cases(settings) == []

    def test_common_and_megapolis_cases(self, tmp_path):
        settings = _make_settings(tmp_path)
        cases = build_generated_qr_cases(settings)
        names = [c.name for c in cases]
        assert names == ["common", "megapolis"]
        for case in cases:
            assert Path(case.image_path).is_file()
            assert case.payload

    def test_disable_megapolis(self, tmp_path):
        settings = _make_settings(tmp_path, QR_MEGAPOLIS_ENABLED="false")
        cases = build_generated_qr_cases(settings)
        assert [c.name for c in cases] == ["common"]
