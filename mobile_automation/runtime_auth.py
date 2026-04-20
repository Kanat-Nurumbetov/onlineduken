from __future__ import annotations

import dataclasses
import json
import re
import subprocess
import time
from pathlib import Path

import requests

from mobile_automation.config import Settings, normalize_b2b_auth_url


def _extract_auth_url(raw_output: str) -> str:
    def extract_from_value(value, key_hint: str = "") -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            for key, nested_value in value.items():
                auth_url = extract_from_value(nested_value, str(key))
                if auth_url:
                    return auth_url
            return ""
        if isinstance(value, list):
            for item in value:
                auth_url = extract_from_value(item, key_hint)
                if auth_url:
                    return auth_url
            return ""
        if not isinstance(value, str):
            value = str(value)

        stripped_value = value.strip()
        if not stripped_value:
            return ""

        if stripped_value.startswith("{") or stripped_value.startswith("["):
            try:
                parsed_nested = json.loads(stripped_value)
            except json.JSONDecodeError:
                parsed_nested = None
            if parsed_nested is not None:
                auth_url = extract_from_value(parsed_nested, key_hint)
                if auth_url:
                    return auth_url

        url_match = re.search(r"https?://\S+", stripped_value)
        if url_match:
            return normalize_b2b_auth_url(raw_url=url_match.group(0).strip())

        normalized_key = key_hint.strip().lower().replace("-", "_")
        if normalized_key in {"ob_auth_token", "token", "access_token"}:
            return normalize_b2b_auth_url(raw_token=stripped_value)

        return ""

    stripped = raw_output.strip()
    if not stripped:
        return ""

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None

    if parsed is not None:
        auth_url = extract_from_value(parsed)
        if auth_url:
            return auth_url

    url_match = re.search(r"https?://\S+", stripped)
    if url_match:
        return normalize_b2b_auth_url(raw_url=url_match.group(0).strip())

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if len(lines) == 1 and " " not in lines[0]:
        return normalize_b2b_auth_url(raw_token=lines[0])

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
    return normalize_b2b_auth_url(raw_url=str(payload.get("auth_url", "")).strip())


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
            "B2B auth fetch command failed "
            f"with exit code {completed.returncode}. STDERR: {stderr or '<empty>'}"
        )

    auth_url = _extract_auth_url(stdout)
    if not auth_url:
        raise RuntimeError(
            "B2B auth fetch command did not return a usable auth URL or token. "
            f"STDOUT: {stdout or '<empty>'}"
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
        raise RuntimeError(
            "Internal B2B login is configured incompletely. Missing: "
            + ", ".join(missing)
        )

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
        auth_url = _extract_auth_url(json.dumps(response.json(), ensure_ascii=False))
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
        payload = {
            "current_url": "",
            "document_url": "",
            "cookie": "",
            "document_cookie": "",
            "local_storage": {},
            "session_storage": {},
        }
        try:
            payload["current_url"] = driver.current_url
        except Exception:
            pass
        try:
            payload["document_url"] = driver.execute_script("return window.location.href;") or ""
        except Exception:
            pass
        try:
            payload["document_cookie"] = driver.execute_script("return document.cookie;") or ""
        except Exception:
            pass
        try:
            payload["local_storage"] = driver.execute_script(
                """
                const out = {};
                for (let i = 0; i < window.localStorage.length; i += 1) {
                  const key = window.localStorage.key(i);
                  out[key] = window.localStorage.getItem(key);
                }
                return out;
                """
            ) or {}
        except Exception:
            pass
        try:
            payload["session_storage"] = driver.execute_script(
                """
                const out = {};
                for (let i = 0; i < window.sessionStorage.length; i += 1) {
                  const key = window.sessionStorage.key(i);
                  out[key] = window.sessionStorage.getItem(key);
                }
                return out;
                """
            ) or {}
        except Exception:
            pass

        auth_url = _extract_auth_url(json.dumps(payload, ensure_ascii=False))
        if auth_url:
            return auth_url

        capture_web_debug_state(driver, "app_auth_bootstrap_no_token_found")
        return ""
    finally:
        driver.quit()


def resolve_shared_b2b_auth_url(settings: Settings) -> str:
    direct_auth_url = settings.resolved_b2b_auth_url
    if direct_auth_url:
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
            continue
        if auth_url:
            save_cached_auth_url(settings, auth_url, source=source)
            return auth_url

    return ""
