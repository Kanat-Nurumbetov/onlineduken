"""Shared smoke-suite helpers.

Prefixed with `_` so pytest does not collect it as a test module while still
importable from sibling test files.
"""

from __future__ import annotations

import contextlib

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation import js as js_snippets
from mobile_automation.flows import click_web_element, open_onlineduken_route
from mobile_automation.pages.native import B2BWebViewPage
from mobile_automation.pages.web import CartPage, CatalogPage, OnlineDukenHomePage, OrderResultPage
from mobile_automation.text_utils import normalize_text

CART_FLOW_SKIP_REASON = (
    "Cart/order smoke is temporarily skipped until a stable supplier with predictable catalog data "
    "is prepared for this environment."
)


def wait(driver, locator: tuple[str, str], timeout: int = 30):
    return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))


def get_qr_case(generated_qr_cases, case_name: str):
    for case in generated_qr_cases:
        if case.name == case_name:
            return case
    return None


def main_text(driver) -> str:
    return normalize_text(driver.execute_script(js_snippets.load("main_content_text")))


def catalog_route_loaded(driver) -> bool:
    return any(
        marker in driver.current_url
        for marker in ("/web/customer-frontend/distributor", "/web/customer-frontend/distributors")
    )


def click_catalog_tab(driver) -> bool:
    try:
        click_web_element(driver, OnlineDukenHomePage.CATALOG_TAB, timeout=15)
        return True
    except TimeoutException:
        return bool(driver.execute_script(js_snippets.load("click_catalog_anchor")))


def open_catalog(driver) -> None:
    if not click_catalog_tab(driver):
        for route_suffix in ("distributors", "distributor"):
            try:
                open_onlineduken_route(driver, route_suffix)
                if catalog_route_loaded(driver):
                    return
            except TimeoutException:
                continue
        raise TimeoutException("Catalog route could not be opened.")

    WebDriverWait(driver, 30).until(lambda current_driver: catalog_route_loaded(current_driver))


def catalog_page_is_ready(driver) -> bool:
    if driver.find_elements(*CatalogPage.TITLE):
        return True
    if driver.find_elements(*CatalogPage.EMPTY_STATE):
        return True
    if driver.find_elements(*CatalogPage.SUPPLIER_CARDS):
        return True
    if driver.find_elements(*CatalogPage.ROOT):
        return True
    page_source = driver.page_source
    return "hb2b-distributor" in page_source or "search-centered" in page_source


def click_first_visible_button_by_text(driver, button_text: str) -> bool:
    return bool(driver.execute_script(js_snippets.load("click_visible_button_by_text"), button_text))


def click_first_matching_element(driver, locator: tuple[str, str]) -> bool:
    elements = driver.find_elements(*locator)
    if not elements:
        return False
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
    elements[0].click()
    return True


def select_first_store_if_needed(driver) -> bool:
    text = main_text(driver).lower()
    if "выберите точку" not in text:
        return False

    xpaths = [
        "//*[contains(normalize-space(), 'QQQQQ')]/ancestor::*[contains(@class, 'item')][1]",
        "//*[contains(normalize-space(), 'QQQQQ')]/ancestor::*[contains(@class, 'address')][1]",
        "//*[contains(normalize-space(), 'QQQQQ')]/ancestor::*[contains(@class, 'store')][1]",
        "//*[contains(normalize-space(), 'QQQQQ')]",
    ]
    for xpath in xpaths:
        elements = driver.find_elements(By.XPATH, xpath)
        if not elements:
            continue
        with contextlib.suppress(WebDriverException, TimeoutException):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
            elements[0].click()
            WebDriverWait(driver, 10).until(
                lambda current_driver: "выберите точку" not in main_text(current_driver).lower()
            )
            return True
    return False


def resolve_quantity_popup_if_present(driver) -> bool:
    text = main_text(driver).lower()
    if "выберите количество товара" not in text and "добавить" not in text:
        return False
    if click_first_visible_button_by_text(driver, "Добавить"):
        WebDriverWait(driver, 10).until(
            lambda current_driver: "выберите количество товара" not in main_text(current_driver).lower()
        )
        return True
    return False


def click_first_catalog_content(driver) -> bool:
    return bool(driver.execute_script(js_snippets.load("click_first_catalog_content")))


def add_product_to_cart_from_catalog(driver, max_depth: int = 8) -> bool:
    for _ in range(max_depth):
        if click_first_matching_element(driver, CatalogPage.ADD_TO_CART_BUTTONS) or click_first_visible_button_by_text(
            driver, "В корзину"
        ):
            resolve_quantity_popup_if_present(driver)
            return True
        if click_first_matching_element(driver, CatalogPage.CREATE_ORDER_BUTTONS) or click_first_visible_button_by_text(
            driver, "Создать заказ"
        ):
            select_first_store_if_needed(driver)
            WebDriverWait(driver, 10).until(lambda current_driver: bool(main_text(current_driver)))
            continue
        if click_first_catalog_content(driver):
            WebDriverWait(driver, 10).until(lambda current_driver: bool(main_text(current_driver)))
            continue
        break
    return False


def open_cart(driver) -> None:
    try:
        click_web_element(driver, OnlineDukenHomePage.CART_TAB, timeout=15)
    except TimeoutException:
        opened = driver.execute_script(js_snippets.load("click_cart_anchor"))
        if not opened:
            open_onlineduken_route(driver, "cart")

    WebDriverWait(driver, 30).until(lambda current_driver: "/web/customer-frontend/cart" in current_driver.current_url)


def cart_has_checkout_state(driver) -> bool:
    text = main_text(driver).lower()
    return bool(driver.find_elements(*CartPage.CREATE_ORDER_BUTTON)) and "нет товаров" not in text


def submit_order_from_cart(driver) -> bool:
    if not click_first_visible_button_by_text(driver, "Создать заказ"):
        return False

    def _order_result_visible(current_driver) -> bool:
        text = main_text(current_driver).lower()
        has_return = bool(current_driver.find_elements(*OrderResultPage.RETURN_TO_ORDERS_BUTTON)) or "вернуть" in text
        has_order_signal = "заказ" in text and ("сформ" in text or "создан" in text or "вернут" in text)
        return has_return and has_order_signal

    WebDriverWait(driver, 30).until(_order_result_visible)
    return True


def onlineduken_native_container_ready(driver) -> bool:
    if driver.find_elements(*B2BWebViewPage.WEBVIEW):
        return True
    current_activity = getattr(driver, "current_activity", "") or ""
    if "B2BActivity" in current_activity:
        return True
    return any(
        marker in (context or "").lower()
        for context in getattr(driver, "contexts", [])
        for marker in ("webview_kz.halyk.onlinebank.stage", "halyk", "onlinebank")
    )
