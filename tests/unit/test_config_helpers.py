from __future__ import annotations

import pytest

from mobile_automation.config import (
    LocalAndroidDevice,
    Settings,
    get_settings,
    is_valid_b2b_auth_url,
    normalize_b2b_auth_url,
    parse_local_android_device_matrix,
)


class TestNormalizeAuthUrl:
    def test_url_without_query_gets_defaults(self):
        url = normalize_b2b_auth_url(
            raw_url="https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=abc"
        )
        assert "lang=ru" in url
        assert "navigateTo=home" in url
        assert "ob-auth-token=abc" in url

    def test_url_preserves_existing_query_params(self):
        url = normalize_b2b_auth_url(
            raw_url="https://b2b.test.onlinebank.kz/web/customer-frontend/auth"
            "?ob-auth-token=abc&lang=kz&navigateTo=orders"
        )
        assert "lang=kz" in url
        assert "navigateTo=orders" in url

    def test_token_only_builds_full_url(self):
        url = normalize_b2b_auth_url(raw_token="abc-token")
        assert url.startswith("https://b2b.test.onlinebank.kz/web/customer-frontend/auth")
        assert "ob-auth-token=abc-token" in url

    def test_empty_inputs_return_empty(self):
        assert normalize_b2b_auth_url() == ""


class TestIsValidAuthUrl:
    def test_valid_url(self):
        url = normalize_b2b_auth_url(raw_token="abc")
        assert is_valid_b2b_auth_url(url)

    def test_missing_token_invalid(self):
        assert not is_valid_b2b_auth_url("https://b2b.test.onlinebank.kz/web/customer-frontend/auth?lang=ru")

    def test_wrong_path_invalid(self):
        assert not is_valid_b2b_auth_url("https://b2b.test.onlinebank.kz/other/path?ob-auth-token=abc")

    def test_empty_invalid(self):
        assert not is_valid_b2b_auth_url("")


class TestParseLocalDeviceMatrix:
    def test_empty_matrix(self):
        assert parse_local_android_device_matrix("") == []
        assert parse_local_android_device_matrix("   ") == []

    def test_single_device(self):
        result = parse_local_android_device_matrix("emulator-5554|http://127.0.0.1:4723")
        assert result == [LocalAndroidDevice("emulator-5554", "http://127.0.0.1:4723")]

    def test_multiple_devices(self):
        result = parse_local_android_device_matrix(
            "emulator-5554|http://127.0.0.1:4723; emulator-5556|http://127.0.0.1:4733"
        )
        assert len(result) == 2
        assert result[0].udid == "emulator-5554"
        assert result[1].appium_server_url == "http://127.0.0.1:4733"

    def test_missing_separator_raises(self):
        with pytest.raises(ValueError, match="must use the format"):
            parse_local_android_device_matrix("emulator-5554")

    def test_missing_part_raises(self):
        with pytest.raises(ValueError, match="must include both"):
            parse_local_android_device_matrix("emulator-5554|")


class TestAppiumNoResetFlag:
    @pytest.fixture(autouse=True)
    def _clear_cache(self, monkeypatch):
        # Drop both env override and the cached Settings so each test sees a clean slate.
        monkeypatch.delenv("APPIUM_NO_RESET", raising=False)
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_default_is_false(self):
        # Off by default — Halyk stage build can wedge UIAutomator2 between sessions.
        assert Settings().appium_no_reset is False

    def test_override_to_true(self, monkeypatch):
        monkeypatch.setenv("APPIUM_NO_RESET", "true")
        assert Settings().appium_no_reset is True

    def test_truthy_strings(self, monkeypatch):
        for value in ("1", "true", "yes", "on", "TRUE"):
            monkeypatch.setenv("APPIUM_NO_RESET", value)
            assert Settings().appium_no_reset is True, f"expected truthy for {value!r}"
