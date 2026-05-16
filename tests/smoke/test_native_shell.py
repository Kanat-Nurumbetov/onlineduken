from __future__ import annotations

import allure
import pytest
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.flows import (
    ensure_expected_contract_selected,
    try_complete_login,
    wait_for_any,
    wait_for_main_home,
)
from mobile_automation.pages.native import LoginPage, MainHomePage, PasscodePage
from tests.smoke._smoke_helpers import onlineduken_native_container_ready


@allure.epic("OnlineDuken")
@allure.feature("BrowserStack Safe Smoke")
@allure.story("Native Shell")
@allure.title("Complete login and reach the native main home")
@pytest.mark.smoke
@pytest.mark.native
@pytest.mark.browserstack_safe
def test_smoke_app_shell_is_reachable(driver, settings):
    with allure.step("Wait for login or main shell"):
        locator = WebDriverWait(driver, 30).until(
            lambda current_driver: wait_for_any(
                current_driver,
                [
                    LoginPage.PHONE_INPUT,
                    PasscodePage.INPUT,
                    MainHomePage.CONTRACT_SELECTOR,
                    MainHomePage.ONLINE_DUKEN_SHORTCUT,
                    MainHomePage.ONLINE_DUKEN_SECTION,
                ],
                timeout=2,
            )
        )
        assert locator is not None

    with allure.step("Complete login if the auth flow is visible"):
        if locator in {LoginPage.PHONE_INPUT, PasscodePage.INPUT}:
            try_complete_login(driver, settings)

    with allure.step("Reach native main home and confirm contract context"):
        assert wait_for_main_home(driver, timeout=45, raise_on_timeout=False), "Main home screen was not detected."
        ensure_expected_contract_selected(driver, settings)
        assert wait_for_any(
            driver,
            [
                MainHomePage.CONTRACT_SELECTOR,
                MainHomePage.ONLINE_DUKEN_SHORTCUT,
                MainHomePage.ONLINE_DUKEN_SECTION,
            ],
            timeout=10,
        ) in {
            MainHomePage.CONTRACT_SELECTOR,
            MainHomePage.ONLINE_DUKEN_SHORTCUT,
            MainHomePage.ONLINE_DUKEN_SECTION,
        }


@allure.epic("OnlineDuken")
@allure.feature("BrowserStack Safe Smoke")
@allure.story("Native Shell")
@allure.title("Reach OnlineDuken native container")
@pytest.mark.smoke
@pytest.mark.native
@pytest.mark.browserstack_safe
def test_smoke_onlineduken_native_container_entry(onlineduken_native_shell_driver):
    with allure.step("Verify that the native OnlineDuken WebView container is present"):
        WebDriverWait(onlineduken_native_shell_driver, 15).until(
            lambda current_driver: onlineduken_native_container_ready(current_driver)
        )
