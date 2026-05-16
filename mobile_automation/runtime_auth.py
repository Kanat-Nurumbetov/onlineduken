from __future__ import annotations

import dataclasses
import json
import logging
import re
import subprocess
import time
from pathlib import Path

import requests
from selenium.common.exceptions import WebDriverException

from mobile_automation import js as js_snippets
from mobile_automation.config import Settings, is_valid_b2b_auth_url, normalize_b2b_auth_url

logger = logging.getLogger(__name__)


_TOKEN_KEYS = {"ob_auth_token", "token", "access_token"}


def _extract_from_value(value, key_hint: str = "") -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key, nested_value in value.items():
            auth_url = _extract_from_value(nested_value, str(key))
            if auth_url:
                return auth_url
        return ""
    if isinstance(value, list):
        for item in value:
            auth_url = _extract_from_value(item, key_hint)
            if auth_url:
                return auth_url
        return ""
    if not isinstance(value, str):
        value = str(value)

    stripped_value = value.strip()
    if not stripped_value:
        return ""

    if stripped_value.startswith(("{", "[")):
        try:
            parsed_nested = json.loads(stripped_value)
        except json.JSONDecodeError:
            parsed_nested = None
        if parsed_nested is not None:
            auth_url = _extract_from_value(parsed_nested, key_hint)
            if auth_url:
                return auth_url

    url_match = re.search(r"https?://\S+", stripped_value)
    if url_match:
        auth_url = normalize_b2b_auth_url(raw_url=url_match.group(0).strip())
        return auth_url if is_valid_b2b_auth_url(auth_url) else ""

    normalized_key = key_hint.strip().lower().replace("-", "_")
    if normalized_key in _TOKEN_KEYS:
        auth_url = normalize_b2b_auth_url(raw_token=stripped_value)
        return auth_url if is_valid_b2b_auth_url(auth_url) else ""

    return ""


def _extract_auth_url(raw_output: str) -> str:
    stripped = raw_output.strip()
    if not stripped:
        return ""

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None

    if parsed is not None:
        auth_url = _extract_from_value(parsed)
        if auth_url:
            return auth_url

    url_match = re.search(r"https?://\S+", stripped)
    if url_match:
        auth_url = normalize_b2b_auth_url(raw_url=url_match.group(0).strip())
        return auth_url if is_valid_b2b_auth_url(auth_url) else ""

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if len(lines) == 1 and " " not in lines[0]:
        auth_url = normalize_b2b_auth_url(raw_token=lines[0])
        return auth_url if is_valid_b2b_auth_url(auth_url) else ""

    return ""


def load_cached_auth_url(settings: Settings) -> str:
    cache_path = Path(settings.b2b_auth_cache_path)
    if not cache_path.exists():
        return ""
    if settings.b2b_auth_cache_ttl_sec > 0:
        age_sec = time.time() - cache_path.stat().st_mtime
        if age_sec > settings.b2b_auth_cache_ttl_sec:
            return ""
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    auth_url = normalize_b2b_auth_url(raw_url=str(payload.get("auth_url", "")).strip())
    return auth_url if is_valid_b2b_auth_url(auth_url) else ""


def save_cached_auth_url(settings: Settings, auth_url: str, source: str) -> None:
    cache_path = Path(settings.b2b_auth_cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "auth_url": auth_url,
        "source": source,
        "saved_at_epoch": int(time.time()),
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def fetch_auth_url_with_command(settings: Settings) -> str:
    if not settings.b2b_auth_fetch_command:
        return ""

    completed = subprocess.run(
        settings.b2b_auth_fetch_command,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        raise RuntimeError(
            "B2B auth fetch command failed " f"with exit code {completed.returncode}. STDERR: {stderr or '<empty>'}"
        )

    auth_url = _extract_auth_url(stdout)
    if not auth_url:
        raise RuntimeError(
            "B2B auth fetch command did not return a usable auth URL or token. " f"STDOUT: {stdout or '<empty>'}"
        )
    return auth_url


def fetch_auth_url_with_internal_login(settings: Settings) -> str:
    if not settings.b2b_internal_login_url:
        return ""

    missing = [
        name
        for name, value in (
            ("B2B_INTERNAL_CLIENT_ID", settings.b2b_internal_client_id),
            ("B2B_INTERNAL_CLIENT_SECRET", settings.b2b_internal_client_secret),
            ("B2B_INTERNAL_GRANT_TYPE", settings.b2b_internal_grant_type),
        )
        if not value
    ]
    if missing:
        raise RuntimeError("Internal B2B login is configured incompletely. Missing: " + ", ".join(missing))

    response = requests.post(
        settings.b2b_internal_login_url,
        data={
            "client_id": settings.b2b_internal_client_id,
            "client_secret": settings.b2b_internal_client_secret,
            "grant_type": settings.b2b_internal_grant_type,
        },
        timeout=60,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type.lower():
        auth_url = _extract_from_value(response.json())
        if auth_url:
            return auth_url

    auth_url = _extract_auth_url(response.text)
    if auth_url:
        return auth_url

    raise RuntimeError(
        "Internal B2B login response did not contain a usable auth URL or token. "
        f"Response body: {response.text[:1000]}"
    )


def fetch_auth_url_via_app_login(settings: Settings) -> str:
    if not settings.b2b_app_auth_bootstrap:
        return ""

    from mobile_automation.driver_factory import build_driver
    from mobile_automation.flows import capture_web_debug_state, enter_onlineduken

    bootstrap_settings = dataclasses.replace(
        settings,
        onlineduken_entry_mode="full",
        b2b_auth_url="",
        b2b_ob_auth_token="",
        b2b_internal_login_url="",
        b2b_auth_fetch_command="",
    )

    driver = build_driver(bootstrap_settings, session_name="OnlineDuken auth bootstrap")
    try:
        enter_onlineduken(driver, bootstrap_settings)
        payload = _collect_webview_auth_payload(driver)

        auth_url = _extract_auth_url_from_payload(payload)
        if auth_url:
            return auth_url

        capture_web_debug_state(driver, "app_auth_bootstrap_no_token_found")
        return ""
    finally:
        driver.quit()


def _extract_auth_url_from_payload(payload) -> str:
    return _extract_from_value(payload)


def _safe_js(driver, script: str, default):
    try:
        return driver.execute_script(script) or default
    except WebDriverException:
        logger.debug("auth bootstrap JS probe failed: %s", script.splitlines()[0].strip(), exc_info=True)
        return default


def _collect_webview_auth_payload(driver) -> dict:
    payload: dict = {
        "current_url": "",
        "document_url": "",
        "cookie": "",
        "document_cookie": "",
        "local_storage": {},
        "session_storage": {},
    }
    try:
        payload["current_url"] = driver.current_url
    except WebDriverException:
        logger.debug("auth bootstrap: driver.current_url read failed", exc_info=True)

    payload["document_url"] = _safe_js(driver, "return window.location.href;", "")
    payload["document_cookie"] = _safe_js(driver, "return document.cookie;", "")
    payload["local_storage"] = _safe_js(driver, js_snippets.load("read_local_storage"), {})
    payload["session_storage"] = _safe_js(driver, js_snippets.load("read_session_storage"), {})
    return payload


def resolve_shared_b2b_auth_url(settings: Settings) -> str:
    direct_auth_url = settings.resolved_b2b_auth_url
    if direct_auth_url and is_valid_b2b_auth_url(direct_auth_url):
        save_cached_auth_url(settings, direct_auth_url, source="env")
        return direct_auth_url

    cached_auth_url = load_cached_auth_url(settings)
    if cached_auth_url:
        return cached_auth_url

    for source, resolver in (
        ("internal_login", fetch_auth_url_with_internal_login),
        ("command", fetch_auth_url_with_command),
        ("app_login", fetch_auth_url_via_app_login),
    ):
        try:
            auth_url = resolver(settings)
        except Exception:
            logger.warning("auth resolver %s failed; trying next strategy", source, exc_info=True)
            continue
        if auth_url:
            save_cached_auth_url(settings, auth_url, source=source)
            return auth_url

    return ""
