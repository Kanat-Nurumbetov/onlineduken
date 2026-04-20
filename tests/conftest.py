from __future__ import annotations

import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import pytest
from appium.webdriver.appium_service import AppiumService

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mobile_automation.config import Settings
from mobile_automation.driver_factory import build_driver
from mobile_automation.flows import enter_onlineduken, recover_onlineduken_home
from mobile_automation.qr_assets import build_generated_qr_cases, ensure_qr_image
from mobile_automation.runtime_auth import resolve_shared_b2b_auth_url


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
        except Exception:
            return False

    def get_driver(self, restart: bool = False):
        if restart or not self._is_alive():
            return self.restart()
        return self._driver

    def restart(self):
        if self._driver is not None:
            with suppress(Exception):
                self._driver.quit()
        self._restart_count += 1
        self._driver = build_driver(self.settings, session_name=f"{self.session_name} #{self._restart_count}")
        setattr(self._driver, "_codex_manager", self)
        return self._driver

    @property
    def active_driver(self):
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            with suppress(Exception):
                self._driver.quit()
            self._driver = None


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


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


def _apply_local_worker_device(worker_udid: str, worker_appium_url: str) -> None:
    if worker_udid:
        os.environ["ANDROID_UDID"] = worker_udid
    if worker_appium_url:
        os.environ["APPIUM_SERVER_URL"] = worker_appium_url


def pytest_configure(config: pytest.Config) -> None:
    worker_input = getattr(config, "workerinput", None)
    if worker_input:
        _apply_shared_b2b_auth_url(worker_input.get(SHARED_B2B_AUTH_URL, ""))
        _apply_local_worker_device(
            worker_input.get(LOCAL_WORKER_UDID, ""),
            worker_input.get(LOCAL_WORKER_APPIUM_URL, ""),
        )
        return

    settings = Settings()
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

    settings = Settings()
    local_devices = settings.resolved_local_android_devices
    if settings.is_browserstack or not local_devices:
        return

    worker_id = getattr(node.gateway, "id", "")
    worker_index = int(worker_id.removeprefix("gw")) if worker_id.startswith("gw") else 0
    if worker_index >= len(local_devices):
        return

    node.workerinput[LOCAL_WORKER_UDID] = local_devices[worker_index].udid
    node.workerinput[LOCAL_WORKER_APPIUM_URL] = local_devices[worker_index].appium_server_url


def pytest_sessionstart(session: pytest.Session) -> None:
    if hasattr(session.config, "workerinput"):
        return

    requested_workers = _requested_parallel_workers(session.config)
    if requested_workers <= 1:
        return

    settings = Settings()
    if settings.is_browserstack:
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
            raise RuntimeError(
                f"Local Appium service failed to start. Check log: {appium_log}"
            )

        yield None
    finally:
        if service.is_running:
            service.stop()
        appium_log_handle.close()


@pytest.fixture(scope="function")
def driver(settings: Settings, appium_service):
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


@pytest.fixture(scope="module")
def ui_session_manager(settings: Settings, appium_service):
    manager = ManagedDriverSession(settings, session_name="OnlineDuken UI smoke")
    yield manager
    manager.close()


@pytest.fixture(scope="module")
def payments_session_manager(settings: Settings, appium_service):
    manager = ManagedDriverSession(settings, session_name="OnlineDuken payments smoke")
    yield manager
    manager.close()


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
