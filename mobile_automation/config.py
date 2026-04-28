from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv


load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _csv_env(name: str) -> list[str]:
    raw = _env(name)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


def normalize_b2b_auth_url(raw_url: str = "", raw_token: str = "") -> str:
    if not raw_url and raw_token:
        raw_url = (
            "https://b2b.test.onlinebank.kz/web/customer-frontend/auth"
            f"?ob-auth-token={raw_token}"
        )
    if not raw_url:
        return ""

    parsed = urlparse(raw_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("lang", "ru")
    query.setdefault("navigateTo", "home")
    return urlunparse(parsed._replace(query=urlencode(query)))


def is_valid_b2b_auth_url(raw_url: str) -> bool:
    if not raw_url:
        return False

    parsed = urlparse(raw_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and "/web/customer-frontend/auth" in parsed.path
        and bool(query.get("ob-auth-token"))
    )


class LocalAndroidDevice(NamedTuple):
    udid: str
    appium_server_url: str


class GeneratedQrCase(NamedTuple):
    name: str
    image_path: str
    payload: str


def parse_local_android_device_matrix(raw_matrix: str) -> list[LocalAndroidDevice]:
    devices: list[LocalAndroidDevice] = []
    if not raw_matrix.strip():
        return devices

    for raw_entry in raw_matrix.split(";"):
        entry = raw_entry.strip()
        if not entry:
            continue
        if "|" not in entry:
            raise ValueError(
                "LOCAL_ANDROID_DEVICE_MATRIX entries must use the format "
                "'<udid>|<appium_server_url>' separated by ';'."
            )
        udid, appium_server_url = [part.strip() for part in entry.split("|", 1)]
        if not udid or not appium_server_url:
            raise ValueError(
                "LOCAL_ANDROID_DEVICE_MATRIX entries must include both udid and appium server URL."
            )
        devices.append(LocalAndroidDevice(udid=udid, appium_server_url=appium_server_url))
    return devices


@dataclass(frozen=True)
class Settings:
    target: str = field(default_factory=lambda: _env("TARGET", "local").lower())
    platform: str = field(default_factory=lambda: _env("PLATFORM", "android").lower())
    onlineduken_entry_mode: str = field(default_factory=lambda: _env("ONLINEDUKEN_ENTRY_MODE", "full").lower())

    appium_server_url: str = field(default_factory=lambda: _env("APPIUM_SERVER_URL", "http://127.0.0.1:4723"))
    appium_node_path: str = field(default_factory=lambda: _env("APPIUM_NODE_PATH", r"C:\Program Files\nodejs\node.exe"))
    appium_main_js: str = field(
        default_factory=lambda: _env(
            "APPIUM_MAIN_JS",
            r"C:\Users\Kanat\AppData\Roaming\npm\node_modules\appium\index.js",
        )
    )
    android_sdk_root: str = field(default_factory=lambda: _env("ANDROID_SDK_ROOT", r"C:\Users\Kanat\AppData\Local\Android\Sdk"))
    android_home: str = field(default_factory=lambda: _env("ANDROID_HOME", r"C:\Users\Kanat\AppData\Local\Android\Sdk"))
    android_app_path: str = field(default_factory=lambda: _env("ANDROID_APP_PATH"))
    android_app_package: str = field(default_factory=lambda: _env("ANDROID_APP_PACKAGE", "kz.halyk.onlinebank.stage"))
    android_app_activity: str = field(
        default_factory=lambda: _env(
            "ANDROID_APP_ACTIVITY",
            "kz.halyk.onlinebank.ui_release4.screens.splash.SplashActivity",
        )
    )
    android_device_name: str = field(default_factory=lambda: _env("ANDROID_DEVICE_NAME", "Android Emulator"))
    android_udid: str = field(default_factory=lambda: _env("ANDROID_UDID", "emulator-5554"))
    android_platform_version: str = field(default_factory=lambda: _env("ANDROID_PLATFORM_VERSION"))
    local_android_device_matrix: str = field(default_factory=lambda: _env("LOCAL_ANDROID_DEVICE_MATRIX"))

    ios_app_path: str = field(default_factory=lambda: _env("IOS_APP_PATH"))
    ios_bundle_id: str = field(default_factory=lambda: _env("IOS_BUNDLE_ID"))
    ios_device_name: str = field(default_factory=lambda: _env("IOS_DEVICE_NAME", "iPhone 15"))
    ios_platform_version: str = field(default_factory=lambda: _env("IOS_PLATFORM_VERSION"))

    browserstack_username: str = field(default_factory=lambda: _env("BROWSERSTACK_USERNAME"))
    browserstack_access_key: str = field(default_factory=lambda: _env("BROWSERSTACK_ACCESS_KEY"))
    browserstack_app_android: str = field(default_factory=lambda: _env("BROWSERSTACK_APP_ANDROID"))
    browserstack_app_ios: str = field(default_factory=lambda: _env("BROWSERSTACK_APP_IOS"))
    browserstack_android_device: str = field(default_factory=lambda: _env("BROWSERSTACK_ANDROID_DEVICE", "Samsung Galaxy S24"))
    browserstack_android_os_version: str = field(default_factory=lambda: _env("BROWSERSTACK_ANDROID_OS_VERSION", "14.0"))
    browserstack_ios_device: str = field(default_factory=lambda: _env("BROWSERSTACK_IOS_DEVICE", "iPhone 15"))
    browserstack_ios_os_version: str = field(default_factory=lambda: _env("BROWSERSTACK_IOS_OS_VERSION", "17"))
    browserstack_web_driver_mode: str = field(default_factory=lambda: _env("BROWSERSTACK_WEB_DRIVER_MODE", "mobile").lower())
    browserstack_web_os: str = field(default_factory=lambda: _env("BROWSERSTACK_WEB_OS", "Windows"))
    browserstack_web_os_version: str = field(default_factory=lambda: _env("BROWSERSTACK_WEB_OS_VERSION", "11"))
    browserstack_web_browser: str = field(default_factory=lambda: _env("BROWSERSTACK_WEB_BROWSER", "Chrome"))
    browserstack_web_browser_version: str = field(default_factory=lambda: _env("BROWSERSTACK_WEB_BROWSER_VERSION", "latest"))
    browserstack_project_name: str = field(default_factory=lambda: _env("BROWSERSTACK_PROJECT_NAME", "B2B Mobile Demo"))
    browserstack_build_name: str = field(default_factory=lambda: _env("BROWSERSTACK_BUILD_NAME", "local-dev"))
    browserstack_webview_enabled: bool = field(default_factory=lambda: _bool_env("BROWSERSTACK_WEBVIEW_ENABLED", False))
    browserstack_login_stagger_sec: int = field(default_factory=lambda: int(_env("BROWSERSTACK_LOGIN_STAGGER_SEC", "20")))
    web_browser: str = field(default_factory=lambda: _env("WEB_BROWSER", "chrome").lower())
    web_headless: bool = field(default_factory=lambda: _bool_env("WEB_HEADLESS", False))
    web_base_url: str = field(
        default_factory=lambda: _env("WEB_BASE_URL", "https://b2b.test.onlinebank.kz/web/customer-frontend/")
    )

    phone_number: str = field(default_factory=lambda: _env("PHONE_NUMBER", "7772229999"))
    sms_code: str = field(default_factory=lambda: _env("SMS_CODE", "123456"))
    pin_code: str = field(default_factory=lambda: _env("PIN_CODE", "0000"))
    contract_suffix: str = field(default_factory=lambda: _env("CONTRACT_SUFFIX", "376"))
    b2b_deeplink: str = field(default_factory=lambda: _env("B2B_DEEPLINK", "https://halyk.onlinebank.kz/appLink/b2b/"))
    b2b_auth_url: str = field(default_factory=lambda: _env("B2B_AUTH_URL"))
    b2b_ob_auth_token: str = field(default_factory=lambda: _env("B2B_OB_AUTH_TOKEN"))
    b2b_internal_login_url: str = field(default_factory=lambda: _env("B2B_INTERNAL_LOGIN_URL"))
    b2b_internal_client_id: str = field(default_factory=lambda: _env("B2B_INTERNAL_CLIENT_ID"))
    b2b_internal_client_secret: str = field(default_factory=lambda: _env("B2B_INTERNAL_CLIENT_SECRET"))
    b2b_internal_grant_type: str = field(default_factory=lambda: _env("B2B_INTERNAL_GRANT_TYPE", "internal"))
    b2b_auth_fetch_command: str = field(default_factory=lambda: _env("B2B_AUTH_FETCH_COMMAND"))
    b2b_shared_auth_bootstrap: bool = field(default_factory=lambda: _bool_env("B2B_SHARED_AUTH_BOOTSTRAP", True))
    b2b_app_auth_bootstrap: bool = field(default_factory=lambda: _bool_env("B2B_APP_AUTH_BOOTSTRAP", True))
    b2b_auth_cache_ttl_sec: int = field(default_factory=lambda: int(_env("B2B_AUTH_CACHE_TTL_SEC", "1800")))
    b2b_auth_cache_path: str = field(
        default_factory=lambda: _env(
            "B2B_AUTH_CACHE_PATH",
            str(Path(__file__).resolve().parents[1] / "artifacts" / "runtime" / "b2b_auth.json"),
        )
    )

    default_supplier: str = field(default_factory=lambda: _env("DEFAULT_SUPPLIER", "TOO Mereke"))
    client_bin: str = field(default_factory=lambda: _env("CLIENT_BIN"))
    qr_image_path: str = field(default_factory=lambda: _env("QR_IMAGE_PATH"))
    qr_source_url: str = field(default_factory=lambda: _env("QR_SOURCE_URL"))
    qr_source_payload: str = field(default_factory=lambda: _env("QR_SOURCE_PAYLOAD"))
    qr_generated_image_path: str = field(
        default_factory=lambda: _env(
            "QR_GENERATED_IMAGE_PATH",
            str(Path(__file__).resolve().parents[1] / "artifacts" / "runtime" / "generated_qr.png"),
        )
    )
    qr_amount: str = field(default_factory=lambda: _env("QR_AMOUNT", "1"))
    qr_invoice_id: str = field(default_factory=lambda: _env("QR_INVOICE_ID", "10001"))
    qr_invoice_title: str = field(default_factory=lambda: _env("QR_INVOICE_TITLE", "10001"))
    qr_megapolis_contract: str = field(default_factory=lambda: _env("QR_MEGAPOLIS_CONTRACT", "10001"))
    qr_common_enabled: bool = field(default_factory=lambda: _bool_env("QR_COMMON_ENABLED", True))
    qr_megapolis_enabled: bool = field(default_factory=lambda: _bool_env("QR_MEGAPOLIS_ENABLED", True))
    qr_common_template: str = field(
        default_factory=lambda: _env(
            "QR_COMMON_TEMPLATE",
            'https://public.test.onlinebank.kz/applink/b2b/distributor/101040002039/client/{client_bin}/invoiceId/{invoice_id}/amount/{amount}/invoiceTitle/{invoice_title}',
        )
    )
    qr_megapolis_template: str = field(
        default_factory=lambda: _env(
            "QR_MEGAPOLIS_TEMPLATE",
            "https://homebank.kz/payments/megapolisKZ?contract={contract}&iin={client_bin}&amount={amount}",
        )
    )
    invoice_reference: str = field(default_factory=lambda: _env("INVOICE_REFERENCE"))

    healthcheck_urls: list[str] = field(default_factory=lambda: _csv_env("TEST_ENV_HEALTHCHECK_URLS"))

    implicit_wait_sec: int = 1
    explicit_wait_sec: int = 30

    @property
    def is_android(self) -> bool:
        return self.platform == "android"

    @property
    def is_ios(self) -> bool:
        return self.platform == "ios"

    @property
    def is_browserstack(self) -> bool:
        return self.target == "browserstack"

    @property
    def browserstack_hub_url(self) -> str:
        return "https://hub.browserstack.com/wd/hub"

    @property
    def app_reference(self) -> str:
        if self.is_browserstack:
            return self.browserstack_app_android if self.is_android else self.browserstack_app_ios
        return self.android_app_path if self.is_android else self.ios_app_path

    @property
    def resolved_local_android_devices(self) -> list[LocalAndroidDevice]:
        return parse_local_android_device_matrix(self.local_android_device_matrix)

    @property
    def resolved_b2b_auth_url(self) -> str:
        return normalize_b2b_auth_url(self.b2b_auth_url, self.b2b_ob_auth_token)

    def require(self, *values: tuple[str, str]) -> None:
        missing = [name for name, value in values if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
