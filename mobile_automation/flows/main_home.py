"""Main-home navigation: contract selection, OnlineDuken entry, store popups.

These helpers run in the native NATIVE_APP context. Anything that switches
to the WebView lives in `mobile_automation.flows.webview`.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.android_ids import APP_PACKAGE, TOUCH_OUTSIDE
from mobile_automation.config import Settings
from mobile_automation.flows._helpers import _parse_bounds, wait_for, wait_for_any
from mobile_automation.flows.debug import capture_native_debug_state
from mobile_automation.pages.native import MainHomePage


def click_first_clickable_ancestor_for_text(driver, text_fragment: str) -> bool:
    try:
        root = ET.fromstring(driver.page_source)
    except ET.ParseError:
        return False

    parent_map = {child: parent for parent in root.iter() for child in parent}

    for node in root.iter():
        text = (node.attrib.get("text") or "").strip()
        if text_fragment not in text:
            continue
        current = node
        while current is not None:
            if current.attrib.get("clickable") == "true":
                parsed = _parse_bounds(current.attrib.get("bounds"))
                if parsed:
                    x1, y1, x2, y2 = parsed
                    driver.execute_script("mobile: clickGesture", {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2})
                    time.sleep(2)
                    return True
            current = parent_map.get(current)

    return False


def swipe_up_within_element(driver, locator: tuple[str, str]) -> bool:
    elements = driver.find_elements(*locator)
    if not elements:
        return False
    element = elements[0]
    rect = element.rect
    left = int(rect["x"])
    top = int(rect["y"])
    width = int(rect["width"])
    height = int(rect["height"])
    if width <= 0 or height <= 0:
        return False

    driver.execute_script(
        "mobile: swipeGesture",
        {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "direction": "up",
            "percent": 0.7,
        },
    )
    time.sleep(1.5)
    return True


def choose_first_store_if_present(driver) -> bool:
    """Native (NATIVE_APP context) store picker. The web counterpart lives in
    `webview.choose_first_store_in_webview_if_present`."""
    try:
        root = ET.fromstring(driver.page_source)
    except ET.ParseError:
        return False

    container_classes = {
        "androidx.recyclerview.widget.RecyclerView",
        "android.widget.ListView",
    }
    ignored_ids = {
        "kz.halyk.onlinebank.stage:id/btn_exit",
        "kz.halyk.onlinebank.stage:id/successButtonNext",
        "kz.halyk.onlinebank.stage:id/support_button",
        "kz.halyk.onlinebank.stage:id/branches_button",
    }

    for node in root.iter():
        if node.attrib.get("class") not in container_classes:
            continue

        clickable_candidates: list[tuple[int, int]] = []
        for child in node.iter():
            if child.attrib.get("clickable") != "true":
                continue
            if child.attrib.get("resource-id") in ignored_ids:
                continue
            parsed = _parse_bounds(child.attrib.get("bounds"))
            if not parsed:
                continue
            x1, y1, x2, y2 = parsed
            clickable_candidates.append(((x1 + x2) // 2, (y1 + y2) // 2))

        if clickable_candidates:
            x, y = clickable_candidates[0]
            driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
            time.sleep(2)
            return True

    return False


def wait_for_main_home(driver, timeout: int = 30, raise_on_timeout: bool = True) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        locator = wait_for_any(
            driver,
            [
                MainHomePage.CONTRACT_SELECTOR,
                MainHomePage.ONLINE_DUKEN_SHORTCUT,
                MainHomePage.ONLINE_DUKEN_SECTION,
            ],
            timeout=2,
        )
        if locator:
            return True

        current_activity = getattr(driver, "current_activity", "")
        current_package = getattr(driver, "current_package", "")
        if current_package and current_package != APP_PACKAGE:
            driver.activate_app(APP_PACKAGE)
            time.sleep(3)
            continue
        if current_activity.endswith(".QrActivity"):
            driver.back()
            time.sleep(2)
            continue

        time.sleep(1)

    capture_native_debug_state(driver, "main_home_not_detected")
    if raise_on_timeout:
        raise TimeoutException("Main home screen was not detected after login.")
    return False


def ensure_expected_contract_selected(driver, settings: Settings) -> bool:
    if not settings.contract_suffix:
        return True

    wait_for(driver, MainHomePage.CONTRACT_NAME, timeout=20)
    contract_name = driver.find_element(*MainHomePage.CONTRACT_NAME).text
    if settings.contract_suffix in contract_name:
        return True

    driver.find_element(*MainHomePage.CONTRACT_SELECTOR).click()
    time.sleep(2)

    for _ in range(8):
        if click_first_clickable_ancestor_for_text(driver, settings.contract_suffix):
            WebDriverWait(driver, 15).until(
                lambda current_driver: settings.contract_suffix
                in current_driver.find_element(*MainHomePage.CONTRACT_NAME).text
            )
            return True
        if not swipe_up_within_element(driver, MainHomePage.CONTRACT_LIST):
            break

    capture_native_debug_state(driver, "contract_suffix_not_found")
    if driver.find_elements(By.ID, TOUCH_OUTSIDE):
        driver.find_element(By.ID, TOUCH_OUTSIDE).click()
        time.sleep(1)
    return False


def open_onlineduken_from_main(driver) -> None:
    wait_for_main_home(driver, timeout=10, raise_on_timeout=False)

    for locator in (MainHomePage.ONLINE_DUKEN_SHORTCUT, MainHomePage.ONLINE_DUKEN_SECTION):
        elements = driver.find_elements(*locator)
        if not elements:
            continue
        elements[0].click()
        time.sleep(2)
        return

    if click_first_clickable_ancestor_for_text(driver, "Online"):
        return

    capture_native_debug_state(driver, "onlineduken_entry_not_found")
    raise TimeoutException("OnlineDuken entry point was not found on the main screen.")
