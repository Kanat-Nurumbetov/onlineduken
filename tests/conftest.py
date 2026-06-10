from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import pytest
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import WebDriverException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mobile_automation.config import Settings, get_settings
from mobile_automation.driver_factory import build_driver
from mobile_automation.driver_registry import register as register_driver
from mobile_automation.driver_registry import unregister as unregister_driver
from mobile_automation.flows import enter_onlineduken, recover_onlineduken_home
from mobile_automation.qr_assets import build_generated_qr_cases, ensure_qr_image
from mobile_automation.reporting import allure_enabled, attach_driver_state, attach_text, write_allure_environment
from mobile_automation.runtime_auth import resolve_shared_b2b_auth_url
from mobile_automation.web_driver_factory import build_web_driver
from mobile_automation.web_flows import open_authenticated_onlineduken

SHARED_B2B_AUTH_URL = "shared_b2b_auth_url"
LOCAL_WORKER_UDID = "local_worker_udid"
LOCAL_WORKER_APPIUM_URL = "local_worker_appium_url"


class ManagedDriverSession:
    def __init__(self, settings: Settings, session_name: str):
        self.settings = settings
        self.session_name = session_name
        self._driver = None
        self._restart_count = 0

    def _is_alive(self) -> bool:
        if self._driver is None:
            return False
        try:
            return bool(self._driver.session_id) and bool(self._driver.contexts)
        except WebDriverException:
            return False

    def get_driver(self, restart: bool = False):
        if restart or not self._is_alive():
            return self.restart()
        return self._driver

    def restart(self):
        if self._driver is not None:
            previous_session_id = getattr(self._driver, "session_id", "")
            with suppress(WebDriverException):
                self._driver.quit()
            unregister_driver(previous_session_id)
        self._restart_count += 1
        self._driver = build_driver(self.settings, session_name=f"{self.session_name} #{self._restart_count}")
        register_driver(getattr(self._driver, "session_id", ""), self)
        return self._driver

    @property
    def active_driver(self):
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            previous_session_id = getattr(self._driver, "session_id", "")
            with suppress(WebDriverException):
                self._driver.quit()
            unregister_driver(previous_session_id)
            self._driver = None


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def prepared_qr_image_path(settings: Settings) -> str:
    return ensure_qr_image(settings)


@pytest.fixture(scope="function")
def generated_qr_cases(settings: Settings):
    return build_generated_qr_cases(settings)


def _appium_is_ready(server_url: str) -> bool:
    status_url = f"{server_url.rstrip('/')}/status"
    with suppress(Exception):
        with urlopen(status_url, timeout=3) as response:
            return response.status == 200
    return False


def _requested_parallel_workers(config: pytest.Config) -> int:
    numprocesses = getattr(config.option, "numprocesses", None)
    if numprocesses in (None, 0, "0"):
        return 0
    if numprocesses == "auto":
        return os.cpu_count() or 1
    with suppress(TypeError, ValueError):
        return int(numprocesses)
    return 0


def _apply_shared_b2b_auth_url(shared_auth_url: str) -> None:
    if not shared_auth_url:
        return
    os.environ["B2B_AUTH_URL"] = shared_auth_url
    os.environ.pop("B2B_OB_AUTH_TOKEN", None)
    get_settings.cache_clear()


def _apply_local_worker_device(worker_udid: str, worker_appium_url: str) -> None:
    if worker_udid:
        os.environ["ANDROID_UDID"] = worker_udid
    if worker_appium_url:
        os.environ["APPIUM_SERVER_URL"] = worker_appium_url
    if worker_udid or worker_appium_url:
        get_settings.cache_clear()


def _get_allure_results_dir(config: pytest.Config) -> str:
    with suppress(Exception):
        return config.getoption("--alluredir") or ""
    return ""


def _safe_allure_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "artifact"


def _xdist_worker_index() -> int:
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    if not worker_id.startswith("gw"):
        return 0
    with suppress(ValueError):
        return int(worker_id.removeprefix("gw"))
    return 0


def _stagger_browserstack_login(settings: Settings) -> None:
    if not settings.is_browserstack or settings.onlineduken_entry_mode != "full":
        return
    delay_sec = _xdist_worker_index() * max(settings.browserstack_login_stagger_sec, 0)
    if delay_sec > 0:
        time.sleep(delay_sec)


def pytest_configure(config: pytest.Config) -> None:
    worker_input = getattr(config, "workerinput", None)
    if worker_input:
        _apply_shared_b2b_auth_url(worker_input.get(SHARED_B2B_AUTH_URL, ""))
        _apply_local_worker_device(
            worker_input.get(LOCAL_WORKER_UDID, ""),
            worker_input.get(LOCAL_WORKER_APPIUM_URL, ""),
        )
        return

    settings = get_settings()
    if settings.onlineduken_entry_mode != "token" or not settings.b2b_shared_auth_bootstrap:
        return

    shared_auth_url = resolve_shared_b2b_auth_url(settings)
    if not shared_auth_url:
        return

    _apply_shared_b2b_auth_url(shared_auth_url)
    setattr(config, SHARED_B2B_AUTH_URL, shared_auth_url)


def pytest_configure_node(node) -> None:
    shared_auth_url = getattr(node.config, SHARED_B2B_AUTH_URL, "")
    if shared_auth_url:
        node.workerinput[SHARED_B2B_AUTH_URL] = shared_auth_url

    settings = get_settings()
    local_devices = settings.resolved_local_android_devices
    if settings.is_browserstack or not local_devices:
        return

    worker_id = getattr(node.gateway, "id", "")
    worker_index = int(worker_id.removeprefix("gw")) if worker_id.startswith("gw") else 0
    if worker_index >= len(local_devices):
        return

    node.workerinput[LOCAL_WORKER_UDID] = local_devices[worker_index].udid
    node.workerinput[LOCAL_WORKER_APPIUM_URL] = local_devices[worker_index].appium_server_url


def _markexpr_limits_run_to_web(config: pytest.Config) -> bool:
    # `web and <anything>` can only select web-marked tests, so requiring
    # `web` as a top-level conjunct is a sound (conservative) check.
    markexpr = getattr(config.option, "markexpr", "") or ""
    conjuncts = {part.strip().strip("()") for part in markexpr.split(" and ")}
    return "web" in conjuncts


def pytest_sessionstart(session: pytest.Session) -> None:
    if hasattr(session.config, "workerinput"):
        return

    allure_results_dir = _get_allure_results_dir(session.config)
    if allure_results_dir:
        write_allure_environment(allure_results_dir, Settings())

    requested_workers = _requested_parallel_workers(session.config)
    if requested_workers <= 1:
        return

    settings = get_settings()
    if settings.is_browserstack:
        return

    if _markexpr_limits_run_to_web(session.config):
        # Browser-only runs never touch Android devices, so the local
        # device matrix does not constrain them.
        return

    local_devices = settings.resolved_local_android_devices
    if len(local_devices) >= requested_workers:
        return

    pytest.exit(
        "Parallel pytest workers were requested for TARGET=local, but there are not "
        "enough configured local devices. Set LOCAL_ANDROID_DEVICE_MATRIX with one "
        "'<udid>|<appium_server_url>' entry per worker, or switch to TARGET=browserstack.",
        returncode=2,
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    settings = get_settings()
    if not settings.is_browserstack or settings.browserstack_webview_enabled:
        return

    skip_reason = (
        "BrowserStack smoke is temporarily split into native-shell checks only. "
        "WebView and payment flows stay disabled until a build with explicit "
        "OnlineDuken WebView debugging is available."
    )
    browserstack_skip = pytest.mark.skip(reason=skip_reason)

    for item in items:
        if "browserstack_safe" in item.keywords:
            continue
        if "webview" in item.keywords or "payments" in item.keywords:
            item.add_marker(browserstack_skip)


def _extract_driver_candidate(value):
    if value is None:
        return None
    if hasattr(value, "session_id") and hasattr(value, "page_source"):
        return value
    active_driver = getattr(value, "active_driver", None)
    if active_driver is not None and hasattr(active_driver, "session_id") and hasattr(active_driver, "page_source"):
        return active_driver
    return None


def _iter_unique_drivers(item: pytest.Item):
    seen: set[str] = set()
    for value in getattr(item, "funcargs", {}).values():
        driver = _extract_driver_candidate(value)
        if driver is None:
            continue
        driver_key = getattr(driver, "session_id", "") or str(id(driver))
        if driver_key in seen:
            continue
        seen.add(driver_key)
        yield driver


def _mark_browserstack_session(driver, status: str, reason: str) -> None:
    payload = {
        "action": "setSessionStatus",
        "arguments": {
            "status": status,
            "reason": reason[:250],
        },
    }
    with suppress(Exception):
        driver.execute_script("browserstack_executor: " + json.dumps(payload))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if get_settings().is_browserstack and report.when in {"setup", "call"}:
        if report.failed:
            reason = report.longreprtext if hasattr(report, "longreprtext") else str(report.longrepr)
            for driver in _iter_unique_drivers(item):
                _mark_browserstack_session(driver, "failed", reason or f"{item.name} failed")
        elif report.when == "call" and report.passed:
            for driver in _iter_unique_drivers(item):
                _mark_browserstack_session(driver, "passed", f"{item.name} passed")

    if not allure_enabled():
        return
    if report.when not in {"setup", "call"} or not report.failed or getattr(report, "wasxfail", False):
        return

    attach_text(f"{report.when}_failure", report.longreprtext)
    for index, driver in enumerate(_iter_unique_drivers(item), start=1):
        attach_driver_state(driver, label_prefix=f"{report.when}_{_safe_allure_name(item.name)}_{index}")


@pytest.fixture(scope="session")
def appium_service(settings: Settings):
    if settings.is_browserstack:
        yield None
        return

    settings.require(
        ("APPIUM_NODE_PATH", settings.appium_node_path),
        ("APPIUM_MAIN_JS", settings.appium_main_js),
        ("ANDROID_SDK_ROOT", settings.android_sdk_root),
    )

    appium_env = os.environ.copy()
    appium_env["ANDROID_SDK_ROOT"] = settings.android_sdk_root
    appium_env["ANDROID_HOME"] = settings.android_home or settings.android_sdk_root
    path_entries = appium_env.get("PATH", "").split(os.pathsep)
    for extra_path in (
        settings.android_sdk_root,
        str(Path(settings.android_sdk_root) / "platform-tools"),
        str(Path(settings.android_sdk_root) / "emulator"),
    ):
        if extra_path and extra_path not in path_entries:
            path_entries.insert(0, extra_path)
    appium_env["PATH"] = os.pathsep.join(path_entries)

    if _appium_is_ready(settings.appium_server_url):
        yield None
        return

    parsed_server_url = urlparse(settings.appium_server_url)
    appium_host = parsed_server_url.hostname or "127.0.0.1"
    appium_port = parsed_server_url.port or 4723
    appium_base_path = parsed_server_url.path or "/"
    worker_suffix = os.getenv("PYTEST_XDIST_WORKER", "main")
    artifacts_dir = ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    appium_log = artifacts_dir / f"appium_pytest_{worker_suffix}_{appium_port}.log"
    appium_log_handle = appium_log.open("a", encoding="utf-8")
    service = AppiumService()
    try:
        service.start(
            args=[
                "--address",
                appium_host,
                "--port",
                str(appium_port),
                "--base-path",
                appium_base_path,
                "--log-level",
                "debug",
            ],
            env=appium_env,
            node=settings.appium_node_path,
            main_script=settings.appium_main_js,
            stdout=appium_log_handle,
            stderr=subprocess.STDOUT,
            timeout_ms=30000,
        )
        if not service.is_running:
            raise RuntimeError(f"Local Appium service failed to start. Check log: {appium_log}")

        yield None
    finally:
        if service.is_running:
            service.stop()
        appium_log_handle.close()


@pytest.fixture(scope="function")
def driver(settings: Settings, appium_service):
    _stagger_browserstack_login(settings)
    driver = build_driver(settings, session_name="OnlineDuken smoke")
    yield driver
    with suppress(Exception):
        driver.quit()


def _prepare_managed_onlineduken_home(manager: ManagedDriverSession, settings: Settings, capture_prefix: str):
    last_error: Exception | None = None
    for attempt_index in range(3):
        restart = attempt_index > 0
        driver = manager.get_driver(restart=restart)
        try:
            recover_onlineduken_home(
                driver,
                settings,
                capture_prefix=f"{capture_prefix}_{'restart' if restart else 'reuse'}_{attempt_index + 1}",
            )
            return driver
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("Managed driver could not be prepared for OnlineDuken.")


@pytest.fixture(scope="function")
def auth_smoke_driver(driver, settings: Settings):
    enter_onlineduken(driver, settings)
    return driver


@pytest.fixture(scope="function")
def onlineduken_native_shell_driver(driver, settings: Settings):
    enter_onlineduken(driver, settings, switch_to_webview_context=False)
    return driver


@pytest.fixture(scope="session")
def web_auth_url(settings: Settings) -> str:
    auth_url = resolve_shared_b2b_auth_url(settings)
    if not auth_url:
        pytest.skip(
            "OnlineDuken web suite requires a resolved auth URL or token. "
            "Set B2B_AUTH_URL/B2B_OB_AUTH_TOKEN or configure internal auth bootstrap."
        )
    return auth_url


@pytest.fixture(scope="function")
def web_driver(settings: Settings, web_auth_url: str):
    try:
        driver = build_web_driver(settings, session_name="OnlineDuken web suite")
    except WebDriverException as exc:
        if settings.is_browserstack and "Automate testing time expired" in str(exc):
            pytest.skip(
                "BrowserStack web session could not be created because the current account "
                "does not have active Automate time available."
            )
        raise
    try:
        open_authenticated_onlineduken(driver, web_auth_url)
        yield driver
    finally:
        with suppress(Exception):
            driver.quit()


def _module_session_manager(settings: Settings, session_label: str):
    manager = ManagedDriverSession(settings, session_name=f"OnlineDuken {session_label}")
    try:
        yield manager
    finally:
        manager.close()


@pytest.fixture(scope="module")
def ui_session_manager(settings: Settings, appium_service):
    yield from _module_session_manager(settings, "UI smoke")


@pytest.fixture(scope="module")
def payments_session_manager(settings: Settings, appium_service):
    yield from _module_session_manager(settings, "payments smoke")


@pytest.fixture(scope="function")
def ui_smoke_driver(ui_session_manager: ManagedDriverSession, settings: Settings):
    driver = _prepare_managed_onlineduken_home(ui_session_manager, settings, "ui_smoke_prepare")
    yield driver
    with suppress(Exception):
        if ui_session_manager.active_driver is not None:
            recover_onlineduken_home(ui_session_manager.active_driver, settings, capture_prefix="ui_smoke_cleanup")


@pytest.fixture(scope="function")
def payments_smoke_driver(payments_session_manager: ManagedDriverSession, settings: Settings):
    driver = _prepare_managed_onlineduken_home(payments_session_manager, settings, "payments_smoke_prepare")
    yield driver
    with suppress(Exception):
        if payments_session_manager.active_driver is not None:
            recover_onlineduken_home(
                payments_session_manager.active_driver,
                settings,
                capture_prefix="payments_smoke_cleanup",
            )
