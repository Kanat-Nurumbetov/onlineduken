from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.config import Settings
from mobile_automation.pages.native import B2BWebViewPage, LoginPage, MainHomePage, MainPromptPage, PasscodePage, SmsCodePage

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
KNOWN_STORE_MARKERS = (
    "QQQQQ",
    "0455b1fd-7001-4417-ac6c-f3897d98bce8",
)
AUTH_RETRY_DIALOG_MARKERS = (
    "Истек код",
    "Повторите запрос",
    "expired",
    "authorization",
)


def wait_for(driver, locator: tuple[str, str], timeout: int = 30):
    return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))


def wait_for_any(driver, locators: list[tuple[str, str]], timeout: int = 10) -> tuple[str, str] | None:
    end = time.time() + timeout
    while time.time() < end:
        for locator in locators:
            if driver.find_elements(*locator):
                return locator
        time.sleep(0.5)
    return None


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
    except Exception:
        pass
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
    bounds_match = re.search(
        r'resource-id="kz\.halyk\.onlinebank\.stage:id/passcode_fragment_keyboard".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
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
                bounds = current.attrib.get("bounds")
                if bounds:
                    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
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
            bounds = child.attrib.get("bounds")
            if not bounds:
                continue
            match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if not match:
                continue
            x1, y1, x2, y2 = map(int, match.groups())
            clickable_candidates.append(((x1 + x2) // 2, (y1 + y2) // 2))

        if clickable_candidates:
            x, y = clickable_candidates[0]
            driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
            time.sleep(2)
            return True

    return False


def is_auth_flow_visible(driver) -> bool:
    return any(
        (
            driver.find_elements(*LoginPage.PHONE_INPUT),
            driver.find_elements(*SmsCodePage.CODE_INPUT),
            driver.find_elements(*PasscodePage.INPUT),
        )
    )


def wait_until_auth_flow_finishes(driver, timeout: int = 20) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if not is_auth_flow_visible(driver):
            return True
        time.sleep(1)
    return False


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
        if current_package and current_package != "kz.halyk.onlinebank.stage":
            driver.activate_app("kz.halyk.onlinebank.stage")
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
                lambda current_driver: settings.contract_suffix in current_driver.find_element(*MainHomePage.CONTRACT_NAME).text
            )
            return True
        if not swipe_up_within_element(driver, MainHomePage.CONTRACT_LIST):
            break

    capture_native_debug_state(driver, "contract_suffix_not_found")
    if driver.find_elements(By.ID, "kz.halyk.onlinebank.stage:id/touch_outside"):
        driver.find_element(By.ID, "kz.halyk.onlinebank.stage:id/touch_outside").click()
        time.sleep(1)
    return False


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


def unlock_if_needed(driver, settings: Settings) -> None:
    if driver.find_elements(By.ID, "kz.halyk.onlinebank.stage:id/pinEditText") and get_pin_value(driver) != settings.pin_code:
        fill_pin_with_virtual_keyboard(driver, settings.pin_code)


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
        has_progress = bool(driver.find_elements(By.ID, "kz.halyk.onlinebank.stage:id/full_progress"))
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


def capture_native_debug_state(driver, prefix: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = ARTIFACTS_DIR / f"{prefix}.png"
    source_path = ARTIFACTS_DIR / f"{prefix}.xml"
    meta_path = ARTIFACTS_DIR / f"{prefix}.txt"

    screenshot_saved = False
    with meta_path.open("w", encoding="utf-8") as meta_file:
        for label, getter in (
            ("current_activity", lambda: getattr(driver, "current_activity", "")),
            ("current_package", lambda: getattr(driver, "current_package", "")),
            ("contexts", lambda: ",".join(driver.contexts)),
        ):
            try:
                meta_file.write(f"{label}={getter()}\n")
            except Exception as exc:  # pragma: no cover - debug helper only
                meta_file.write(f"{label}=<error: {exc}>\n")

        try:
            source_path.write_text(driver.page_source, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"page_source_error={exc}\n")

        try:
            screenshot_saved = driver.get_screenshot_as_file(str(screenshot_path))
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"screenshot_error={exc}\n")

        meta_file.write(f"screenshot_saved={screenshot_saved}\n")
        meta_file.write(f"screenshot_path={screenshot_path}\n")
        meta_file.write(f"source_path={source_path}\n")


def capture_web_debug_state(driver, prefix: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    source_path = ARTIFACTS_DIR / f"{prefix}.html"
    meta_path = ARTIFACTS_DIR / f"{prefix}.txt"
    screenshot_path = ARTIFACTS_DIR / f"{prefix}.png"

    with meta_path.open("w", encoding="utf-8") as meta_file:
        for label, getter in (
            ("current_url", lambda: driver.current_url),
            ("title", lambda: driver.title),
            ("current_context", lambda: getattr(driver, "current_context", "")),
        ):
            try:
                meta_file.write(f"{label}={getter()}\n")
            except Exception as exc:  # pragma: no cover - debug helper only
                meta_file.write(f"{label}=<error: {exc}>\n")

        try:
            source_path.write_text(driver.page_source, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"page_source_error={exc}\n")

        try:
            screenshot_saved = driver.get_screenshot_as_file(str(screenshot_path))
        except Exception as exc:  # pragma: no cover - debug helper only
            screenshot_saved = False
            meta_file.write(f"screenshot_error={exc}\n")

        meta_file.write(f"screenshot_saved={screenshot_saved}\n")
        meta_file.write(f"screenshot_path={screenshot_path}\n")
        meta_file.write(f"source_path={source_path}\n")


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
    raise TimeoutException("WEBVIEW context was not found. Debug artifacts saved to artifacts/webview_context_timeout.*")


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
            overlay_present = driver.execute_script(
                """
                const overlay = document.querySelector('.bottom-overlay__fade');
                if (!overlay) return false;
                const style = window.getComputedStyle(overlay);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                """
            )
            if not overlay_present:
                return True
        except Exception:
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

    clicked_visible_store = driver.execute_script(
        """
        const selectors = [
          '.bottom-overlay.bottom-overlay_visible .user-addresses__item',
          '.bottom-overlay.bottom-overlay_visible .user-addresses__item-inner'
        ];
        for (const selector of selectors) {
          const candidates = Array.from(document.querySelectorAll(selector));
          for (const candidate of candidates) {
            const rect = candidate.getBoundingClientRect();
            if (!rect.width || !rect.height) {
              continue;
            }
            candidate.scrollIntoView({block: 'center'});
            candidate.click();
            return (candidate.innerText || candidate.textContent || '').trim();
          }
        }
        return '';
        """
    )
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

    clicked_text = driver.execute_script(
        """
        const skipPattern = /закрыть|close|cancel|отмена/i;
        const roots = Array.from(
          document.querySelectorAll('[class*="bottom-overlay"], [class*="store"], [class*="shop"], [class*="branch"]')
        );
        for (const root of roots) {
          const candidates = root.querySelectorAll('button, a, [role="button"], [onclick], .item, .card');
          for (const candidate of candidates) {
            const text = (candidate.innerText || candidate.textContent || '').trim();
            if (!text || skipPattern.test(text)) {
              continue;
            }
            const rect = candidate.getBoundingClientRect();
            if (!rect.width || !rect.height) {
              continue;
            }
            candidate.scrollIntoView({block: 'center'});
            candidate.click();
            return text;
          }
        }
        return '';
        """
    )
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
    except Exception:
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


def recover_onlineduken_home(driver, settings: Settings, max_attempts: int = 2, capture_prefix: str = "onlineduken_home_recovery") -> None:
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            try:
                ensure_webview_context(driver, timeout=10)
                open_onlineduken_home(driver)
                return
            except Exception as exc:
                last_error = exc

            try:
                switch_to_native(driver)
            except Exception as exc:
                last_error = exc

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
                except Exception as exc:
                    last_error = exc
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
            except Exception:
                pass

    try:
        current_context = getattr(driver, "current_context", "")
    except Exception:
        current_context = ""
    if "WEBVIEW" in current_context.upper():
        capture_web_debug_state(driver, capture_prefix)
    else:
        capture_native_debug_state(driver, capture_prefix)
    if last_error:
        raise last_error
    raise TimeoutException("Failed to recover OnlineDuken home state.")


def wait_for_web_customer_frontend(driver, timeout: int = 30) -> None:
    WebDriverWait(driver, timeout).until(
        lambda current_driver: "/web/customer-frontend/" in current_driver.current_url
    )


def apply_b2b_auth_url_in_webview(driver, settings: Settings) -> bool:
    if not settings.resolved_b2b_auth_url:
        return False
    driver.get(settings.resolved_b2b_auth_url)
    wait_for_web_customer_frontend(driver, timeout=30)
    choose_first_store_in_webview_if_present(driver)
    return True


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
            ready_state = wait_for_post_deeplink_ready_state(driver, settings, timeout=max(settings.explicit_wait_sec, 45))
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
