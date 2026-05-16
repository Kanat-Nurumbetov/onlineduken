"""OnlineDuken entry orchestration.

The two public entry points are:
- `enter_onlineduken` — initial path from a freshly launched app
- `recover_onlineduken_home` — best-effort recovery between tests in a shared
  `ManagedDriverSession`

Both compose the smaller flows from `auth`, `main_home`, and `webview`.
"""

from __future__ import annotations

import logging
import time

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.android_ids import FULL_PROGRESS
from mobile_automation.config import Settings
from mobile_automation.flows.auth import (
    dismiss_post_login_prompts,
    fill_pin_with_virtual_keyboard,
    get_pin_value,
    is_auth_flow_visible,
    try_complete_login,
    unlock_if_needed,
)
from mobile_automation.flows.debug import capture_native_debug_state, capture_web_debug_state
from mobile_automation.flows.main_home import (
    choose_first_store_if_present,
    ensure_expected_contract_selected,
    open_onlineduken_from_main,
    wait_for_main_home,
)
from mobile_automation.flows.webview import (
    choose_first_store_in_webview_if_present,
    ensure_webview_context,
    has_target_b2b_webview,
    switch_to_native,
    switch_to_webview,
)
from mobile_automation.pages.native import B2BWebViewPage, MainPromptPage, PasscodePage
from mobile_automation.web_flows import wait_for_customer_frontend as wait_for_web_customer_frontend

logger = logging.getLogger(__name__)


def open_b2b_deeplink(driver, settings: Settings) -> None:
    if not settings.is_android:
        raise RuntimeError("B2B deeplink helper is currently configured for Android only.")
    driver.execute_script(
        "mobile:deepLink",
        {"url": settings.b2b_deeplink, "package": settings.android_app_package},
    )


def open_b2b_auth_url(driver, settings: Settings) -> None:
    if not settings.resolved_b2b_auth_url:
        raise RuntimeError("B2B auth URL is not configured.")
    if not settings.is_android:
        raise RuntimeError("B2B auth URL helper is currently configured for Android only.")
    driver.execute_script(
        "mobile:deepLink",
        {"url": settings.resolved_b2b_auth_url, "package": settings.android_app_package},
    )


def wait_for_post_deeplink_ready_state(driver, settings: Settings, timeout: int = 45) -> str:
    end = time.time() + timeout
    stagnant_since = time.time()
    previous_state: tuple[str, str, bool, bool, bool] | None = None

    while time.time() < end:
        if has_target_b2b_webview(driver, settings):
            return "webview"
        if driver.find_elements(*MainPromptPage.NEXT_BUTTON):
            driver.find_element(*MainPromptPage.NEXT_BUTTON).click()
            stagnant_since = time.time()
            time.sleep(1.5)
            continue
        if choose_first_store_if_present(driver):
            stagnant_since = time.time()
            continue
        has_passcode = bool(driver.find_elements(*PasscodePage.INPUT))
        pin_value = get_pin_value(driver)
        has_progress = bool(driver.find_elements(By.ID, FULL_PROGRESS))
        has_webview = bool(driver.find_elements(*B2BWebViewPage.WEBVIEW))
        current_state = (getattr(driver, "current_activity", ""), pin_value, has_passcode, has_progress, has_webview)

        if current_state != previous_state:
            previous_state = current_state
            stagnant_since = time.time()

        if has_passcode and pin_value != settings.pin_code:
            fill_pin_with_virtual_keyboard(driver, settings.pin_code)
            stagnant_since = time.time()
            time.sleep(2)
            continue
        if has_passcode and pin_value == settings.pin_code and has_progress and time.time() - stagnant_since >= 12:
            return "retry_deeplink"
        if has_progress:
            time.sleep(2)
            continue
        if not has_passcode:
            return "native_ready"
        time.sleep(1)
    return "timeout"


def open_onlineduken_home(driver) -> None:
    ensure_webview_context(driver, timeout=15)
    route_marker = "/web/customer-frontend/"
    current_url = driver.current_url
    if route_marker in current_url:
        home_url = current_url.split(route_marker, 1)[0] + route_marker
    else:
        home_url = "https://b2b.test.onlinebank.kz/web/customer-frontend/"
    driver.get(home_url)
    WebDriverWait(driver, 30).until(lambda current_driver: route_marker in current_driver.current_url)
    choose_first_store_in_webview_if_present(driver)


def open_onlineduken_route(driver, route_suffix: str) -> None:
    ensure_webview_context(driver, timeout=15)
    route_marker = "/web/customer-frontend/"
    current_url = driver.current_url
    if route_marker in current_url:
        base_url = current_url.split(route_marker, 1)[0] + route_marker
    else:
        base_url = "https://b2b.test.onlinebank.kz/web/customer-frontend/"
    target_url = base_url + route_suffix.lstrip("/")
    driver.get(target_url)
    WebDriverWait(driver, 30).until(lambda current_driver: route_marker in current_driver.current_url)
    choose_first_store_in_webview_if_present(driver)


def apply_b2b_auth_url_in_webview(driver, settings: Settings) -> bool:
    if not settings.resolved_b2b_auth_url:
        return False
    driver.get(settings.resolved_b2b_auth_url)
    wait_for_web_customer_frontend(driver, timeout=30)
    choose_first_store_in_webview_if_present(driver)
    return True


def recover_onlineduken_home(
    driver,
    settings: Settings,
    max_attempts: int = 2,
    capture_prefix: str = "onlineduken_home_recovery",
) -> None:
    last_error: Exception | None = None

    for _attempt in range(max_attempts):
        try:
            try:
                ensure_webview_context(driver, timeout=10)
                open_onlineduken_home(driver)
                return
            except Exception as exc:
                last_error = exc

            try:
                switch_to_native(driver)
            except WebDriverException as exc:
                last_error = exc
                logger.debug("switch_to_native failed during recovery", exc_info=True)

            dismiss_post_login_prompts(driver, timeout=3)

            if is_auth_flow_visible(driver):
                try_complete_login(driver, settings)

            if choose_first_store_if_present(driver):
                time.sleep(1)

            for _ in range(3):
                try:
                    if driver.find_elements(*B2BWebViewPage.WEBVIEW):
                        break
                    driver.back()
                    time.sleep(1)
                except WebDriverException as exc:
                    last_error = exc
                    logger.debug("driver.back() failed while seeking B2B webview", exc_info=True)
                    break

            try:
                if has_target_b2b_webview(driver, settings):
                    switch_to_webview(driver, timeout=15, settings=settings)
                    open_onlineduken_home(driver)
                    return
            except Exception as exc:
                last_error = exc

            enter_onlineduken(driver, settings)
            open_onlineduken_home(driver)
            return
        except Exception as exc:
            last_error = exc
            try:
                driver.activate_app(settings.android_app_package)
                time.sleep(2)
            except WebDriverException:
                logger.debug("activate_app fallback failed during recovery", exc_info=True)

    try:
        current_context = getattr(driver, "current_context", "")
    except WebDriverException:
        logger.debug("current_context read failed after recovery attempts", exc_info=True)
        current_context = ""
    if "WEBVIEW" in current_context.upper():
        capture_web_debug_state(driver, capture_prefix)
    else:
        capture_native_debug_state(driver, capture_prefix)
    if last_error:
        raise last_error
    raise TimeoutException("Failed to recover OnlineDuken home state.")


def enter_onlineduken(driver, settings: Settings, switch_to_webview_context: bool = True) -> None:
    if settings.onlineduken_entry_mode == "token":
        ready_state = "timeout"
        if settings.resolved_b2b_auth_url:
            entry_strategies = [lambda current_driver: open_b2b_auth_url(current_driver, settings)]
            if settings.b2b_deeplink:
                entry_strategies.append(lambda current_driver: open_b2b_deeplink(current_driver, settings))
        else:
            entry_strategies = []

        for open_strategy in entry_strategies:
            try:
                open_strategy(driver)
            except (TimeoutException, RuntimeError, WebDriverException):
                continue
            time.sleep(3)
            unlock_if_needed(driver, settings)
            ready_state = wait_for_post_deeplink_ready_state(
                driver, settings, timeout=max(settings.explicit_wait_sec, 45)
            )
            if ready_state == "webview":
                break
            time.sleep(2)

        if ready_state != "webview":
            if is_auth_flow_visible(driver):
                try_complete_login(driver, settings)

            native_home_ready = wait_for_main_home(
                driver,
                timeout=max(settings.explicit_wait_sec, 30),
                raise_on_timeout=False,
            )
            if native_home_ready:
                ensure_expected_contract_selected(driver, settings)

            for open_strategy in (
                open_onlineduken_from_main if native_home_ready else None,
                (lambda current_driver: open_b2b_deeplink(current_driver, settings)) if settings.b2b_deeplink else None,
            ):
                if open_strategy is None:
                    continue
                try:
                    open_strategy(driver)
                except (TimeoutException, RuntimeError, WebDriverException):
                    continue
                time.sleep(3)
                unlock_if_needed(driver, settings)
                ready_state = wait_for_post_deeplink_ready_state(
                    driver,
                    settings,
                    timeout=max(settings.explicit_wait_sec, 45),
                )
                if ready_state == "webview":
                    break
                dismiss_post_login_prompts(driver, timeout=5)
                time.sleep(2)

        if not has_target_b2b_webview(driver, settings):
            capture_native_debug_state(driver, f"missing_b2b_webview_container_{ready_state}")
        if not switch_to_webview_context:
            return
        switch_to_webview(driver, timeout=settings.explicit_wait_sec, settings=settings)
        if settings.resolved_b2b_auth_url:
            apply_b2b_auth_url_in_webview(driver, settings)
        choose_first_store_in_webview_if_present(driver)
        return

    try_complete_login(driver, settings)
    native_home_ready = wait_for_main_home(driver, timeout=max(settings.explicit_wait_sec, 30), raise_on_timeout=False)
    if native_home_ready:
        ensure_expected_contract_selected(driver, settings)

    ready_state = "timeout"
    entry_strategies = [lambda current_driver: open_b2b_deeplink(current_driver, settings)]
    if native_home_ready:
        entry_strategies.insert(0, open_onlineduken_from_main)

    for open_strategy in entry_strategies:
        try:
            open_strategy(driver)
        except TimeoutException:
            continue
        time.sleep(3)
        unlock_if_needed(driver, settings)
        ready_state = wait_for_post_deeplink_ready_state(driver, settings, timeout=max(settings.explicit_wait_sec, 45))
        if ready_state == "webview":
            break
        dismiss_post_login_prompts(driver, timeout=5)
        time.sleep(2)

    if not has_target_b2b_webview(driver, settings):
        capture_native_debug_state(driver, f"missing_b2b_webview_container_{ready_state}")
    if not switch_to_webview_context:
        return
    switch_to_webview(driver, timeout=settings.explicit_wait_sec, settings=settings)
    choose_first_store_in_webview_if_present(driver)
