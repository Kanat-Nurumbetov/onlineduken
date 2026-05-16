"""WebView context juggling for the OnlineDuken hybrid app.

The Halyk shell wraps the OnlineDuken WebView, so half the smoke suite has
to switch back and forth between NATIVE_APP and WEBVIEW_kz.halyk... contexts.
This module owns that dance plus the store-picker bottom sheet that appears
once the WebView is reachable.
"""

from __future__ import annotations

import logging
import time

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

from mobile_automation import js as js_snippets
from mobile_automation.config import Settings
from mobile_automation.flows.debug import capture_native_debug_state, capture_web_debug_state
from mobile_automation.pages.native import B2BWebViewPage

logger = logging.getLogger(__name__)

KNOWN_STORE_MARKERS = (
    "QQQQQ",
    "0455b1fd-7001-4417-ac6c-f3897d98bce8",
)


def _app_webview_contexts(driver, settings: Settings) -> list[str]:
    package_name = (settings.android_app_package or "").lower()
    matched_contexts: list[str] = []
    for context in getattr(driver, "contexts", []):
        normalized_context = context.lower()
        if "webview" not in normalized_context:
            continue
        if package_name and package_name in normalized_context:
            matched_contexts.append(context)
            continue
        if "halyk" in normalized_context or "onlinebank" in normalized_context:
            matched_contexts.append(context)
    return matched_contexts


def has_target_b2b_webview(driver, settings: Settings) -> bool:
    if driver.find_elements(*B2BWebViewPage.WEBVIEW):
        return True
    return bool(_app_webview_contexts(driver, settings))


def switch_to_webview(driver, timeout: int = 30, settings: Settings | None = None) -> str:
    end = time.time() + timeout
    while time.time() < end:
        prioritized_contexts = []
        if settings is not None:
            prioritized_contexts.extend(_app_webview_contexts(driver, settings))

        seen_contexts = set(prioritized_contexts)
        for context in driver.contexts:
            if context in seen_contexts:
                continue
            prioritized_contexts.append(context)

        for context in prioritized_contexts:
            if "WEBVIEW" in context.upper():
                driver.switch_to.context(context)
                return context
        time.sleep(1)
    capture_native_debug_state(driver, "webview_context_timeout")
    raise TimeoutException(
        "WEBVIEW context was not found. Debug artifacts saved to artifacts/webview_context_timeout.*"
    )


def switch_to_native(driver) -> None:
    driver.switch_to.context("NATIVE_APP")


def ensure_webview_context(driver, timeout: int = 15, settings: Settings | None = None) -> None:
    current_context = getattr(driver, "current_context", "")
    if "WEBVIEW" in current_context.upper():
        return
    switch_to_webview(driver, timeout=timeout, settings=settings)


def wait_for_web_overlay_to_clear(driver, timeout: int = 10) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            overlay_present = driver.execute_script(js_snippets.load("overlay_visible"))
            if not overlay_present:
                return True
        except WebDriverException:
            logger.debug("overlay JS probe failed; falling back to page_source check", exc_info=True)
            if "bottom-overlay__fade" not in driver.page_source:
                return True
        time.sleep(0.5)
    return False


def choose_first_store_in_webview_if_present(driver) -> bool:
    source = driver.page_source
    has_visible_overlay = "bottom-overlay bottom-overlay_visible" in source
    has_known_store_markers = any(marker in source for marker in KNOWN_STORE_MARKERS)
    has_store_overlay = has_visible_overlay or has_known_store_markers
    if not has_store_overlay:
        return False

    capture_web_debug_state(driver, "web_store_popup_detected")

    clicked_visible_store = driver.execute_script(js_snippets.load("select_store_in_visible_overlay"))
    if clicked_visible_store:
        wait_for_web_overlay_to_clear(driver, timeout=10)
        return True

    for marker in KNOWN_STORE_MARKERS:
        elements = driver.find_elements(By.XPATH, f"//*[contains(normalize-space(), '{marker}')]")
        if not elements:
            continue
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
        driver.execute_script("arguments[0].click();", elements[0])
        wait_for_web_overlay_to_clear(driver, timeout=10)
        return True

    clicked_text = driver.execute_script(js_snippets.load("select_store_fallback"))
    if clicked_text:
        wait_for_web_overlay_to_clear(driver, timeout=10)
        return True

    capture_web_debug_state(driver, "web_store_popup_selection_failed")
    return False


def _is_webview_disconnect_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "invalid session id" in message
        or "devtools" in message
        or "disconnected" in message
        or "browser has closed the connection" in message
    )


def _recover_webview_context(driver) -> bool:
    try:
        switch_to_native(driver)
        switch_to_webview(driver, timeout=15)
        return True
    except (WebDriverException, TimeoutException):
        logger.debug("webview context recovery failed", exc_info=True)
        return False


def wait_for_web_element(driver, locator: tuple[str, str], timeout: int = 30):
    ensure_webview_context(driver, timeout=min(timeout, 15))
    end = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < end:
        try:
            elements = driver.find_elements(*locator)
            if elements:
                return elements[0]
        except WebDriverException as exc:
            last_error = exc
            if _is_webview_disconnect_error(exc) and _recover_webview_context(driver):
                time.sleep(1)
                continue
        time.sleep(0.5)
    if last_error and _is_webview_disconnect_error(last_error):
        capture_native_debug_state(driver, "webview_context_recovery_failed")
    raise TimeoutException(f"Web element was not found within {timeout}s: {locator}")


def click_web_element(driver, locator: tuple[str, str], timeout: int = 30):
    ensure_webview_context(driver, timeout=min(timeout, 15))
    choose_first_store_in_webview_if_present(driver)
    element = wait_for_web_element(driver, locator, timeout=timeout)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)
    except WebDriverException as exc:
        if _is_webview_disconnect_error(exc) and _recover_webview_context(driver):
            element = wait_for_web_element(driver, locator, timeout=timeout)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            driver.execute_script("arguments[0].click();", element)
        else:
            raise
    return element
