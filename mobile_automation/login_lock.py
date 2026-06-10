"""Cross-process mutex for the shared-phone login flow.

Every pytest worker authenticates with the same test phone number, so
concurrent full logins race on the OTP: a worker that requests a fresh SMS
code invalidates the code another worker is about to submit ("auth code
expired after sms entry"). The stagger delay only lowers the probability of
that race; this lock removes it by letting exactly one worker run the
phone/SMS/PIN flow at a time. Everything after login still runs in parallel.

The lock file lives in artifacts/runtime, which all xdist workers on one
machine share. Remote sessions are pinged while a worker waits, because
BrowserStack terminates sessions that stay idle for ~90 seconds.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout
from selenium.common.exceptions import TimeoutException, WebDriverException

from mobile_automation.config import Settings

logger = logging.getLogger(__name__)

# Must stay well under the ~90s BrowserStack idle limit so the waiting
# worker pings its session between acquire attempts.
_ACQUIRE_SLICE_SEC = 10


def _keep_session_alive(driver) -> None:
    try:
        _ = driver.current_package
    except WebDriverException:
        logger.debug("keep-alive ping failed while waiting for the login lock", exc_info=True)


@contextmanager
def hold_login_lock(driver, settings: Settings):
    if not settings.login_lock_enabled:
        yield
        return

    lock_path = Path(settings.login_lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path))
    deadline = time.monotonic() + max(settings.login_lock_timeout_sec, _ACQUIRE_SLICE_SEC)
    waited = False
    while True:
        try:
            lock.acquire(timeout=_ACQUIRE_SLICE_SEC)
            break
        except Timeout:
            waited = True
            if time.monotonic() >= deadline:
                raise TimeoutException(
                    "Could not acquire the shared login lock within "
                    f"{settings.login_lock_timeout_sec}s; another worker is likely "
                    "stuck inside the login flow."
                ) from None
            _keep_session_alive(driver)
    if waited:
        logger.info("Shared login lock acquired after waiting; running serialized login.")
    try:
        yield
    finally:
        lock.release()
