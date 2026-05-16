from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import allure
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.android_ids import app_id
from mobile_automation.config import GeneratedQrCase, Settings
from mobile_automation.driver_registry import get_session_manager_for
from mobile_automation.flows import capture_native_debug_state, enter_onlineduken, recover_onlineduken_home, switch_to_native
from mobile_automation.pages.native import NativePaymentPage, OnlineDukenNativeHomePage, PhotoPickerPage, QrScannerPage
from mobile_automation.text_utils import normalize_text

logger = logging.getLogger(__name__)


def _adb_path(settings: Settings) -> Path:
    adb_name = "adb.exe" if os.name == "nt" else "adb"
    if settings.android_sdk_root:
        candidate = Path(settings.android_sdk_root) / "platform-tools" / adb_name
        if candidate.is_file():
            return candidate
    discovered = shutil.which("adb")
    if discovered:
        return Path(discovered)
    raise RuntimeError(
        "adb executable was not found. Set ANDROID_SDK_ROOT or add adb to PATH."
    )


def _run_adb(settings: Settings, *args: str) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        [str(_adb_path(settings)), "-s", settings.android_udid, *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"ADB command failed: {' '.join(args)}\nSTDOUT: {completed.stdout}\nSTDERR: {completed.stderr}"
        )
    return completed


def push_qr_image_to_local_device(settings: Settings, image_path: str) -> str:
    if not image_path:
        raise RuntimeError("QR image path is empty.")

    source_path = Path(image_path)
    if not source_path.exists():
        raise RuntimeError(f"QR image does not exist: {source_path}")

    target_name = f"codex_{source_path.stem}.png"
    target_path = f"/sdcard/Pictures/{target_name}"
    _run_adb(settings, "shell", "rm", "-f", "/sdcard/Pictures/codex_*.png")
    _run_adb(settings, "push", str(source_path), target_path)
    _run_adb(
        settings,
        "shell",
        "am",
        "broadcast",
        "-a",
        "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d",
        f"file://{target_path}",
    )
    return target_path


def push_qr_image_to_browserstack_device(driver, image_path: str) -> str:
    if not image_path:
        raise RuntimeError("QR image path is empty.")

    source_path = Path(image_path)
    if not source_path.exists():
        raise RuntimeError(f"QR image does not exist: {source_path}")

    target_name = f"codex_{source_path.stem}.png"
    target_path = f"/sdcard/Pictures/{target_name}"
    driver.push_file(target_path, source_path=str(source_path))
    try:
        driver.execute_script(
            "mobile: shell",
            {
                "command": "am",
                "args": [
                    "broadcast",
                    "-a",
                    "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d",
                    f"file://{target_path}",
                ],
                "timeout": 30000,
            },
        )
    except WebDriverException:
        # BrowserStack documents Appium push_file as supported. Media scanner availability can vary;
        # the photo picker often sees pushed Pictures files even when shell is restricted.
        logger.debug("media scanner broadcast failed on BrowserStack; relying on photo picker fallback", exc_info=True)
    return target_path


def push_qr_image_to_device(driver, settings: Settings, image_path: str) -> str:
    if settings.is_browserstack:
        return push_qr_image_to_browserstack_device(driver, image_path)
    return push_qr_image_to_local_device(settings, image_path)


def _wait_for_native_presence(driver, locator: tuple[str, str], timeout: int = 30):
    return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))


def _click_element_center(driver, element) -> None:
    rect = element.rect
    x = int(rect["x"] + rect["width"] / 2)
    y = int(rect["y"] + rect["height"] / 2)
    try:
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
    except WebDriverException:
        logger.debug("mobile: clickGesture failed; falling back to element.click()", exc_info=True)
        element.click()


def accept_android_permission_if_present(driver) -> bool:
    allow_locators = (
        ("id", "com.android.permissioncontroller:id/permission_allow_foreground_only_button"),
        ("id", "com.android.permissioncontroller:id/permission_allow_button"),
        ("xpath", "//*[@text='While using the app' or @text='Allow' or @text='Разрешить']"),
    )
    for by, value in allow_locators:
        elements = driver.find_elements(by, value)
        if not elements:
            continue
        elements[0].click()
        time.sleep(1)
        return True
    return False


def _extract_toast_message(page_source: str) -> str:
    try:
        root = ET.fromstring(page_source)
    except ET.ParseError:
        return ""

    for node in root.iter():
        if node.attrib.get("resource-id") != "toast-container":
            continue
        texts: list[str] = []
        for child in node.iter():
            text = normalize_text(child.attrib.get("text", ""))
            if text.lower() == "close":
                continue
            if text:
                texts.append(text)
        if texts:
            return " ".join(dict.fromkeys(texts))
    return ""


def _is_invalid_bin_toast(message: str) -> bool:
    normalized = normalize_text(message).lower()
    return (
        "бин" in normalized
        or "iin/bin" in normalized
        or "iin" in normalized
        or "bin" in normalized
        or "неправильный" in normalized
        or "неверный" in normalized
    )


def _is_payment_confirmation_screen(page_source: str) -> bool:
    confirmation_markers = tuple(
        f'resource-id="{app_id(short_id)}"' for short_id in ("pinEditText", "et", "sms_subtitle")
    )
    has_confirmation_input = all(marker in page_source for marker in confirmation_markers)
    has_confirmation_title = "РџРѕРґС‚РІРµСЂР¶Рґ" in page_source or "Подтверж" in page_source
    return has_confirmation_input or has_confirmation_title


def open_qr_scanner(driver) -> None:
    last_error: Exception | None = None
    for attempt_index in range(3):
        qr_tab = _wait_for_native_presence(driver, OnlineDukenNativeHomePage.QR_TAB, timeout=30)
        try:
            qr_tab.click()
        except WebDriverException:
            logger.debug("QR_TAB.click() failed; retrying via center gesture", exc_info=True)
            _click_element_center(driver, qr_tab)
        time.sleep(2)
        accept_android_permission_if_present(driver)
        try:
            _wait_for_native_presence(driver, QrScannerPage.GALLERY_BUTTON, timeout=15)
            return
        except TimeoutException as exc:
            last_error = exc
            try:
                _click_element_center(driver, qr_tab)
            except WebDriverException:
                logger.debug("QR_TAB recovery click failed", exc_info=True)
            time.sleep(2)
            accept_android_permission_if_present(driver)
            if driver.find_elements(*QrScannerPage.GALLERY_BUTTON):
                return
    capture_native_debug_state(driver, "qr_scanner_gallery_button_not_found")
    if last_error:
        raise last_error
    raise TimeoutException("QR scanner gallery button was not found.")


def prepare_qr_entry(driver, settings: Settings, qr_case: GeneratedQrCase):
    recover_onlineduken_home(driver, settings, capture_prefix=f"qr_home_recovery_{qr_case.name}")
    switch_to_native(driver)

    if driver.find_elements(*OnlineDukenNativeHomePage.QR_TAB):
        return driver

    for _ in range(2):
        try:
            driver.back()
            time.sleep(1)
        except WebDriverException:
            logger.debug("driver.back() failed while preparing QR entry", exc_info=True)
            break
        if driver.find_elements(*OnlineDukenNativeHomePage.QR_TAB):
            return driver

    try:
        enter_onlineduken(driver, settings)
        switch_to_native(driver)
        if driver.find_elements(*OnlineDukenNativeHomePage.QR_TAB):
            return driver
    except (TimeoutException, WebDriverException):
        logger.warning("enter_onlineduken failed during QR entry preparation; attempting driver restart", exc_info=True)
        manager = get_session_manager_for(driver)
        if manager is not None:
            restarted_driver = manager.restart()
            recover_onlineduken_home(
                restarted_driver,
                settings,
                capture_prefix=f"qr_home_recovery_restart_{qr_case.name}",
            )
            switch_to_native(restarted_driver)
            if restarted_driver.find_elements(*OnlineDukenNativeHomePage.QR_TAB):
                return restarted_driver

    capture_native_debug_state(driver, f"qr_native_home_not_ready_{qr_case.name}")
    raise TimeoutException("QR native home entry point was not detected.")


def open_photo_picker(driver) -> None:
    _wait_for_native_presence(driver, QrScannerPage.GALLERY_BUTTON, timeout=30).click()
    _wait_for_native_presence(driver, PhotoPickerPage.ROOT, timeout=30)
    dismiss_buttons = driver.find_elements(*PhotoPickerPage.DISMISS_BUTTON)
    if dismiss_buttons:
        dismiss_buttons[0].click()
        time.sleep(1)


def select_first_photo(driver) -> None:
    for locator in (PhotoPickerPage.FIRST_PHOTO, PhotoPickerPage.FIRST_GRID_ITEM):
        elements = driver.find_elements(*locator)
        if elements:
            _click_element_center(driver, elements[0])
            return
        try:
            _click_element_center(driver, _wait_for_native_presence(driver, locator, timeout=10))
            return
        except TimeoutException:
            continue
    capture_native_debug_state(driver, "qr_photo_picker_item_not_found")
    raise TimeoutException("No selectable photo was found in the Android photo picker.")


def wait_for_qr_payment_screen(driver, timeout: int = 45) -> None:
    _wait_for_native_presence(driver, NativePaymentPage.PAY_BUTTON, timeout=timeout)


def submit_qr_payment(driver, timeout: int = 15) -> str:
    _wait_for_native_presence(driver, NativePaymentPage.PAY_BUTTON, timeout=20).click()
    starting_activity = getattr(driver, "current_activity", "")
    end = time.time() + timeout

    while time.time() < end:
        page_source = driver.page_source
        toast_message = _extract_toast_message(page_source)
        if toast_message:
            if _is_invalid_bin_toast(toast_message):
                capture_native_debug_state(driver, "qr_payment_invalid_bin_toast")
                raise AssertionError(
                    "QR payment was rejected by backend because the QR contains an invalid client BIN/IIN. "
                    f"Toast: {toast_message}"
                )
            capture_native_debug_state(driver, "qr_payment_unexpected_toast")
            raise AssertionError(f"QR payment produced an unexpected toast: {toast_message}")

        current_activity = getattr(driver, "current_activity", "")
        if current_activity != starting_activity:
            return current_activity

        if _is_payment_confirmation_screen(page_source):
            return "payment_confirmation_screen"

        if not driver.find_elements(*NativePaymentPage.PAY_BUTTON):
            return "pay_button_disappeared"

        time.sleep(1)

    capture_native_debug_state(driver, "qr_payment_submission_not_observed")
    raise AssertionError(
        "After tapping 'Оплатить', the payment screen stayed unchanged and no confirmation or processing state was detected."
    )


def run_qr_gallery_payment_flow(driver, settings: Settings, qr_case: GeneratedQrCase) -> str:
    with allure.step(f"Push generated QR image to device for case '{qr_case.name}'"):
        push_qr_image_to_device(driver, settings, qr_case.image_path)
    with allure.step("Prepare OnlineDuken native home for QR flow"):
        active_driver = prepare_qr_entry(driver, settings, qr_case) or driver
    with allure.step("Open QR scanner"):
        open_qr_scanner(active_driver)
    with allure.step("Open native photo picker"):
        open_photo_picker(active_driver)
    with allure.step("Select the first QR image from gallery"):
        select_first_photo(active_driver)
    with allure.step("Wait for QR payment screen"):
        wait_for_qr_payment_screen(active_driver)
    with allure.step("Submit QR payment"):
        return submit_qr_payment(active_driver)
