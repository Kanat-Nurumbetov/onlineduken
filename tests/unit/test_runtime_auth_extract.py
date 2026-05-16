from __future__ import annotations

import json

from mobile_automation.runtime_auth import _extract_auth_url, _extract_from_value


class TestExtractFromValue:
    def test_url_in_dict(self):
        payload = {"current_url": "https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=xyz"}
        result = _extract_from_value(payload)
        assert "ob-auth-token=xyz" in result
        assert "lang=ru" in result

    def test_token_under_known_key(self):
        payload = {"local_storage": {"ob_auth_token": "token-123"}}
        result = _extract_from_value(payload)
        assert "ob-auth-token=token-123" in result

    def test_nested_json_string(self):
        nested = json.dumps({"access_token": "deep-token"})
        payload = {"document_cookie": nested}
        result = _extract_from_value(payload)
        assert "ob-auth-token=deep-token" in result

    def test_no_token_returns_empty(self):
        assert _extract_from_value({"foo": "bar", "baz": 42}) == ""

    def test_list_traversal(self):
        payload = [{"unrelated": 1}, {"token": "list-token"}]
        result = _extract_from_value(payload)
        assert "ob-auth-token=list-token" in result


class TestExtractAuthUrl:
    def test_plain_url_output(self):
        result = _extract_auth_url(
            "https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=abc trailing text"
        )
        assert "ob-auth-token=abc" in result

    def test_single_line_token(self):
        result = _extract_auth_url("just-a-token")
        assert "ob-auth-token=just-a-token" in result

    def test_empty_input(self):
        assert _extract_auth_url("") == ""
        assert _extract_auth_url("   ") == ""

    def test_json_input(self):
        result = _extract_auth_url(json.dumps({"ob-auth-token": "json-token"}))
        assert "ob-auth-token=json-token" in result

    def test_url_without_token_returns_empty(self):
        result = _extract_auth_url("https://example.com/other/path?lang=ru")
        assert result == ""
