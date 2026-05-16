"""Low-level helpers used across the flows package.

Kept private because nothing outside `mobile_automation.flows.*` should reach
in here. The bounds parser, in particular, exists only because Appium's UIA2
page source serialises rects as `[x1,y1][x2,y2]` and several flow modules
need to compute element centres from that.
"""

from __future__ import annotations

import re

from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.wait_utils import poll_until

_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _parse_bounds(bounds: str | None) -> tuple[int, int, int, int] | None:
    if not bounds:
        return None
    match = _BOUNDS_RE.match(bounds)
    if not match:
        return None
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def wait_for(driver, locator: tuple[str, str], timeout: int = 30):
    return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))


def wait_for_any(driver, locators: list[tuple[str, str]], timeout: int = 10) -> tuple[str, str] | None:
    def find_present() -> tuple[str, str] | None:
        for locator in locators:
            if driver.find_elements(*locator):
                return locator
        return None

    result: tuple[str, str] | None = None

    def predicate() -> bool:
        nonlocal result
        result = find_present()
        return result is not None

    if poll_until(predicate, timeout=timeout, poll=0.5):
        return result
    return None
