from __future__ import annotations

import time
from typing import Callable, TypeVar

from selenium.common.exceptions import TimeoutException

T = TypeVar("T")


def wait_until(
    predicate: Callable[[], T],
    timeout: float = 15.0,
    poll: float = 0.5,
    message: str = "",
) -> T:
    """Poll `predicate` until it returns a truthy value or timeout elapses.

    Returns the truthy value (not just True) so callers can use it as a fetch.
    Raises TimeoutException with `message` if the deadline passes.
    """
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(poll)
    raise TimeoutException(message or f"wait_until timed out after {timeout}s")


def poll_until(
    predicate: Callable[[], bool],
    timeout: float = 15.0,
    poll: float = 0.5,
) -> bool:
    """Like wait_until but returns False on timeout instead of raising."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(poll)
    return False
