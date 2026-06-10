import threading
import time
from types import SimpleNamespace

import pytest
from filelock import FileLock
from selenium.common.exceptions import TimeoutException, WebDriverException

from mobile_automation import login_lock
from mobile_automation.login_lock import hold_login_lock


class FakeDriver:
    def __init__(self, fail_pings: bool = False):
        self.pings = 0
        self._fail_pings = fail_pings

    @property
    def current_package(self):
        self.pings += 1
        if self._fail_pings:
            raise WebDriverException("session gone")
        return "kz.halyk.onlinebank.stage"


def make_settings(tmp_path, **overrides):
    base = {
        "login_lock_enabled": True,
        "login_lock_path": str(tmp_path / "login.lock"),
        "login_lock_timeout_sec": 10,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def hold_in_thread(lock_path: str, hold_sec: float) -> threading.Thread:
    entered = threading.Event()

    def holder():
        with FileLock(lock_path, thread_local=False):
            entered.set()
            time.sleep(hold_sec)

    thread = threading.Thread(target=holder, daemon=True)
    thread.start()
    assert entered.wait(5)
    return thread


def test_disabled_lock_does_not_touch_the_filesystem(tmp_path):
    settings = make_settings(tmp_path, login_lock_enabled=False)
    with hold_login_lock(FakeDriver(), settings):
        pass
    assert not (tmp_path / "login.lock").exists()


def test_lock_is_released_after_use(tmp_path):
    settings = make_settings(tmp_path)
    driver = FakeDriver()
    with hold_login_lock(driver, settings):
        pass
    with hold_login_lock(driver, settings):
        pass
    assert driver.pings == 0


def test_waiting_worker_pings_session_and_then_acquires(tmp_path, monkeypatch):
    monkeypatch.setattr(login_lock, "_ACQUIRE_SLICE_SEC", 0.2)
    settings = make_settings(tmp_path)
    driver = FakeDriver()
    thread = hold_in_thread(settings.login_lock_path, hold_sec=0.8)

    with hold_login_lock(driver, settings):
        pass

    thread.join(5)
    assert driver.pings >= 1


def test_ping_failure_does_not_break_the_wait(tmp_path, monkeypatch):
    monkeypatch.setattr(login_lock, "_ACQUIRE_SLICE_SEC", 0.2)
    settings = make_settings(tmp_path)
    driver = FakeDriver(fail_pings=True)
    thread = hold_in_thread(settings.login_lock_path, hold_sec=0.8)

    with hold_login_lock(driver, settings):
        pass

    thread.join(5)
    assert driver.pings >= 1


def test_raises_timeout_exception_when_holder_never_releases(tmp_path, monkeypatch):
    monkeypatch.setattr(login_lock, "_ACQUIRE_SLICE_SEC", 0.2)
    settings = make_settings(tmp_path, login_lock_timeout_sec=1)
    holder = FileLock(settings.login_lock_path, thread_local=False)
    holder.acquire()
    try:
        with pytest.raises(TimeoutException):
            with hold_login_lock(FakeDriver(), settings):
                pass
    finally:
        holder.release()
