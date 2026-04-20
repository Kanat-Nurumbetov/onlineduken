from __future__ import annotations

import time

import pytest

from mobile_automation.flows import (
    capture_web_debug_state,
    capture_native_debug_state,
    click_web_element,
    dismiss_post_login_prompts,
    enter_onlineduken,
    ensure_expected_contract_selected,
    open_onlineduken_from_main,
    try_complete_login,
    wait_for_main_home,
)
from mobile_automation.pages.web import OnlineDukenHomePage


@pytest.mark.manual
def test_probe_native_home_after_login(driver, settings):
    try_complete_login(driver, settings)
    dismiss_post_login_prompts(driver, timeout=10)
    capture_native_debug_state(driver, "native_home_probe")


@pytest.mark.manual
def test_probe_store_popup_after_onlineduken_tap(driver, settings):
    try_complete_login(driver, settings)
    dismiss_post_login_prompts(driver, timeout=10)
    wait_for_main_home(driver, timeout=30)
    ensure_expected_contract_selected(driver, settings)
    open_onlineduken_from_main(driver)
    time.sleep(3)
    capture_native_debug_state(driver, "store_popup_probe")


@pytest.mark.manual
def test_probe_webview_after_onlineduken_entry(driver, settings):
    enter_onlineduken(driver, settings)
    capture_web_debug_state(driver, "webview_after_onlineduken_entry")


@pytest.mark.manual
def test_probe_bonuses_page(driver, settings):
    enter_onlineduken(driver, settings)
    click_web_element(driver, OnlineDukenHomePage.BONUSES_LINK)
    time.sleep(3)
    capture_web_debug_state(driver, "bonuses_page_probe")


@pytest.mark.manual
def test_probe_catalog_page(driver, settings):
    enter_onlineduken(driver, settings)
    click_web_element(driver, OnlineDukenHomePage.CATALOG_TAB)
    time.sleep(3)
    capture_web_debug_state(driver, "catalog_page_probe")
