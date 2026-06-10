"""Login flow for the Halyk stage Android app.

Covers the phone-number prompt, SMS code, virtual pin keyboard, the retry
dialog that surfaces when codes expire, and the post-login prompt screens.

`try_complete_login` is the orchestrator the rest of the suite uses;
`unlock_if_needed` is the lighter sibling for runs where only the passcode
gate is in the way (e.g. after a deeplink lands on a backgrounded session).
"""

from __future__ import annotations

import logging
import re
import time

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

from mobile_automation.android_ids import PASSCODE_KEYBOARD, PIN_EDIT_TEXT
from mobile_automation.config import Settings
from mobile_automation.flows._helpers import wait_for_any
from mobile_automation.flows.debug import capture_native_debug_state
from mobile_automation.login_lock import hold_login_lock
from mobile_automation.pages.native import LoginPage, MainPromptPage, PasscodePage, SmsCodePage
from mobile_automation.wait_utils import poll_until

logger = logging.getLogger(__name__)

AUTH_RETRY_DIALOG_MARKERS = (
    "Истек код",
    "Повторите запрос",
    "expired",
    "authorization",
)


def get_pin_value(driver) -> str:
    fields = driver.find_elements(*PasscodePage.INPUT)
    if not fields:
        return ""
    return (fields[0].get_attribute("text") or fields[0].text or "").strip()


def fill_text_input(driver, locator: tuple[str, str], value: str) -> bool:
    elements = driver.find_elements(*locator)
    if not elements:
        return False
    field = elements[0]
    field.click()
    try:
        field.clear()
    except WebDriverException:
        logger.debug("clear() failed on %s; relying on send_keys to overwrite", locator, exc_info=True)
    field.send_keys(value)
    return True


def is_sms_confirmation_screen(driver) -> bool:
    return bool(driver.find_elements(*SmsCodePage.SUBTITLE) or driver.find_elements(*SmsCodePage.TIMER))


def is_passcode_screen(driver) -> bool:
    return bool(driver.find_elements(*PasscodePage.INPUT)) and not is_sms_confirmation_screen(driver)


def fill_pin_with_virtual_keyboard(driver, pin: str) -> None:
    keypad_layout = {
        "1": (0, 0),
        "2": (1, 0),
        "3": (2, 0),
        "4": (0, 1),
        "5": (1, 1),
        "6": (2, 1),
        "7": (0, 2),
        "8": (1, 2),
        "9": (2, 2),
        "0": (1, 3),
    }
    source = driver.page_source
    keyboard_id_pattern = re.escape(PASSCODE_KEYBOARD)
    bounds_match = re.search(
        rf'resource-id="{keyboard_id_pattern}".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        source,
        re.DOTALL,
    )
    if not bounds_match:
        if not driver.find_elements(*PasscodePage.INPUT):
            return
        capture_native_debug_state(driver, "missing_passcode_keyboard")
        raise TimeoutException("Passcode keyboard bounds were not found in page source.")
    x1, y1, x2, y2 = map(int, bounds_match.groups())
    col_width = (x2 - x1) / 3
    row_height = (y2 - y1) / 4

    for digit in pin:
        col, row = keypad_layout[digit]
        x = int(x1 + (col + 0.5) * col_width)
        y = int(y1 + (row + 0.5) * row_height)
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        time.sleep(0.2)


def dismiss_post_login_prompts(driver, timeout: int = 15) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if driver.find_elements(*MainPromptPage.NEXT_BUTTON):
            driver.find_element(*MainPromptPage.NEXT_BUTTON).click()
            time.sleep(1.5)
            continue
        break


def is_auth_flow_visible(driver) -> bool:
    return any(
        (
            driver.find_elements(*LoginPage.PHONE_INPUT),
            driver.find_elements(*SmsCodePage.CODE_INPUT),
            driver.find_elements(*PasscodePage.INPUT),
        )
    )


def wait_until_auth_flow_finishes(driver, timeout: int = 20) -> bool:
    return poll_until(lambda: not is_auth_flow_visible(driver), timeout=timeout, poll=1.0)


def dismiss_auth_retry_dialog_if_present(driver) -> bool:
    messages = driver.find_elements(By.ID, "android:id/message")
    if not messages:
        return False
    message = (messages[0].get_attribute("text") or messages[0].text or "").strip()
    normalized_message = message.lower()
    if not any(marker.lower() in normalized_message for marker in AUTH_RETRY_DIALOG_MARKERS):
        return False

    buttons = driver.find_elements(By.ID, "android:id/button1")
    if buttons:
        buttons[0].click()
    else:
        driver.press_keycode(4)
    time.sleep(1.5)
    return True


def try_complete_login(driver, settings: Settings) -> None:
    # The whole retry loop stays under one lock: every retry re-requests an
    # SMS code, so two workers interleaving retries still poison each other.
    with hold_login_lock(driver, settings):
        _try_complete_login_serialized(driver, settings)


def _try_complete_login_serialized(driver, settings: Settings) -> None:
    last_retry_reason = ""
    for attempt_index in range(3):
        if dismiss_auth_retry_dialog_if_present(driver):
            last_retry_reason = "auth retry dialog was visible before login attempt"

        if driver.find_elements(*LoginPage.PHONE_INPUT):
            phone_input = driver.find_element(*LoginPage.PHONE_INPUT)
            phone_input.click()
            phone_input.clear()
            phone_input.send_keys(settings.phone_number)
            driver.find_element(*LoginPage.LOGIN_BUTTON).click()
            time.sleep(2)

        wait_for_any(driver, [SmsCodePage.CODE_INPUT, PasscodePage.INPUT], timeout=15)

        if is_sms_confirmation_screen(driver):
            fill_text_input(driver, SmsCodePage.CODE_INPUT, settings.sms_code)
            time.sleep(3)

        if dismiss_auth_retry_dialog_if_present(driver):
            last_retry_reason = "auth code expired after sms entry"
            time.sleep(10 * (attempt_index + 1))
            continue

        for _ in range(3):
            if not is_passcode_screen(driver):
                break
            try:
                fill_pin_with_virtual_keyboard(driver, settings.pin_code)
            except TimeoutException:
                if not fill_text_input(driver, SmsCodePage.CODE_INPUT, settings.pin_code):
                    raise
            time.sleep(2)

        if wait_until_auth_flow_finishes(driver, timeout=20):
            dismiss_post_login_prompts(driver)
            return

        if dismiss_auth_retry_dialog_if_present(driver):
            last_retry_reason = "auth code expired while waiting for auth flow to finish"
            time.sleep(10 * (attempt_index + 1))
            continue

        if driver.find_elements(*LoginPage.PHONE_INPUT):
            last_retry_reason = "login screen was still visible after auth attempt"
            time.sleep(5 * (attempt_index + 1))
            continue
        break

    capture_native_debug_state(driver, "stuck_on_auth_after_login_attempt")
    raise TimeoutException(
        "Login flow did not leave AuthActivity. "
        f"Last retry reason: {last_retry_reason or 'unknown'}. "
        "Debug artifacts saved to artifacts/stuck_on_auth_after_login_attempt.*"
    )


def unlock_if_needed(driver, settings: Settings) -> None:
    if driver.find_elements(By.ID, PIN_EDIT_TEXT) and get_pin_value(driver) != settings.pin_code:
        fill_pin_with_virtual_keyboard(driver, settings.pin_code)
