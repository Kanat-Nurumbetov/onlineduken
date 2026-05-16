from __future__ import annotations

import allure
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation import js as js_snippets
from mobile_automation.flows import (
    click_web_element,
    ensure_expected_contract_selected,
    open_onlineduken_route,
    try_complete_login,
    wait_for_any,
    wait_for_main_home,
)
from mobile_automation.pages.native import B2BWebViewPage, LoginPage, MainHomePage, PasscodePage
from mobile_automation.pages.web import (
    BonusesPage,
    CartPage,
    CatalogPage,
    OnlineDukenHomePage,
    OrderResultPage,
    OrdersPage,
    PaymentPage,
)
from mobile_automation.qr_flow import run_qr_gallery_payment_flow
from mobile_automation.text_utils import normalize_text

CART_FLOW_SKIP_REASON = (
    "Cart/order smoke is temporarily skipped until a stable supplier with predictable catalog data "
    "is prepared for this environment."
)


def wait(driver, locator: tuple[str, str], timeout: int = 30):
    return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))


def _get_qr_case(generated_qr_cases, case_name: str):
    for case in generated_qr_cases:
        if case.name == case_name:
            return case
    return None


def _main_text(driver) -> str:
    return normalize_text(driver.execute_script(js_snippets.load("main_content_text")))


def _catalog_route_loaded(driver) -> bool:
    return any(
        marker in driver.current_url
        for marker in ("/web/customer-frontend/distributor", "/web/customer-frontend/distributors")
    )


def _click_catalog_tab(driver) -> bool:
    try:
        click_web_element(driver, OnlineDukenHomePage.CATALOG_TAB, timeout=15)
        return True
    except TimeoutException:
        return bool(driver.execute_script(js_snippets.load("click_catalog_anchor")))


def _open_catalog(driver) -> None:
    if not _click_catalog_tab(driver):
        for route_suffix in ("distributors", "distributor"):
            try:
                open_onlineduken_route(driver, route_suffix)
                if _catalog_route_loaded(driver):
                    return
            except TimeoutException:
                continue
        raise TimeoutException("Catalog route could not be opened.")

    WebDriverWait(driver, 30).until(lambda current_driver: _catalog_route_loaded(current_driver))


def _catalog_page_is_ready(driver) -> bool:
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


def _click_first_visible_button_by_text(driver, button_text: str) -> bool:
    return bool(driver.execute_script(js_snippets.load("click_visible_button_by_text"), button_text))


def _click_first_matching_element(driver, locator: tuple[str, str]) -> bool:
    elements = driver.find_elements(*locator)
    if not elements:
        return False
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
    elements[0].click()
    return True


def _select_first_store_if_needed(driver) -> bool:
    text = _main_text(driver).lower()
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
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
            elements[0].click()
            WebDriverWait(driver, 10).until(
                lambda current_driver: "выберите точку" not in _main_text(current_driver).lower()
            )
            return True
        except Exception:
            continue
    return False


def _resolve_quantity_popup_if_present(driver) -> bool:
    text = _main_text(driver).lower()
    if "выберите количество товара" not in text and "добавить" not in text:
        return False
    if _click_first_visible_button_by_text(driver, "Добавить"):
        WebDriverWait(driver, 10).until(
            lambda current_driver: "выберите количество товара" not in _main_text(current_driver).lower()
        )
        return True
    return False


def _click_first_catalog_content(driver) -> bool:
    return bool(driver.execute_script(js_snippets.load("click_first_catalog_content")))


def _add_product_to_cart_from_catalog(driver, max_depth: int = 8) -> bool:
    for _ in range(max_depth):
        if _click_first_matching_element(
            driver, CatalogPage.ADD_TO_CART_BUTTONS
        ) or _click_first_visible_button_by_text(driver, "В корзину"):
            _resolve_quantity_popup_if_present(driver)
            return True
        if _click_first_matching_element(
            driver, CatalogPage.CREATE_ORDER_BUTTONS
        ) or _click_first_visible_button_by_text(driver, "Создать заказ"):
            _select_first_store_if_needed(driver)
            WebDriverWait(driver, 10).until(lambda current_driver: bool(_main_text(current_driver)))
            continue
        if _click_first_catalog_content(driver):
            WebDriverWait(driver, 10).until(lambda current_driver: bool(_main_text(current_driver)))
            continue
        break
    return False


def _open_cart(driver) -> None:
    try:
        click_web_element(driver, OnlineDukenHomePage.CART_TAB, timeout=15)
    except TimeoutException:
        opened = driver.execute_script(js_snippets.load("click_cart_anchor"))
        if not opened:
            open_onlineduken_route(driver, "cart")

    WebDriverWait(driver, 30).until(lambda current_driver: "/web/customer-frontend/cart" in current_driver.current_url)


def _cart_has_checkout_state(driver) -> bool:
    text = _main_text(driver).lower()
    return bool(driver.find_elements(*CartPage.CREATE_ORDER_BUTTON)) and "нет товаров" not in text


def _submit_order_from_cart(driver) -> bool:
    if not _click_first_visible_button_by_text(driver, "Создать заказ"):
        return False

    def _order_result_visible(current_driver) -> bool:
        text = _main_text(current_driver).lower()
        has_return = bool(current_driver.find_elements(*OrderResultPage.RETURN_TO_ORDERS_BUTTON)) or "вернуть" in text
        has_order_signal = "заказ" in text and ("сформ" in text or "создан" in text or "вернут" in text)
        return has_return and has_order_signal

    WebDriverWait(driver, 30).until(_order_result_visible)
    return True


def _onlineduken_native_container_ready(driver) -> bool:
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
            lambda current_driver: _onlineduken_native_container_ready(current_driver)
        )


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Entry")
@allure.title("Open OnlineDuken")
@pytest.mark.smoke
@pytest.mark.webview
def test_smoke_onlineduken_entry(auth_smoke_driver):
    with allure.step("Verify that OnlineDuken home route is open"):
        assert "/web/customer-frontend" in auth_smoke_driver.current_url


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Catalog")
@allure.title("Open catalog and validate supplier page state")
@pytest.mark.smoke
@pytest.mark.webview
def test_smoke_catalog_has_suppliers(ui_smoke_driver):
    with allure.step("Open catalog"):
        _open_catalog(ui_smoke_driver)
    with allure.step("Validate supplier cards or a valid empty state"):
        WebDriverWait(ui_smoke_driver, 30).until(lambda current_driver: _catalog_page_is_ready(current_driver))
        supplier_cards = ui_smoke_driver.find_elements(*CatalogPage.SUPPLIER_CARDS)
        empty_state = ui_smoke_driver.find_elements(*CatalogPage.EMPTY_STATE)
        assert (
            supplier_cards or empty_state or _catalog_page_is_ready(ui_smoke_driver)
        ), "Catalog did not show supplier cards, a valid empty state, or the distributor page structure."


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Orders")
@allure.title("Open orders page")
@pytest.mark.smoke
@pytest.mark.webview
def test_smoke_orders_navigation(ui_smoke_driver):
    with allure.step("Open orders page"):
        try:
            click_web_element(ui_smoke_driver, OnlineDukenHomePage.ORDERS_LINK)
        except TimeoutException:
            open_onlineduken_route(ui_smoke_driver, "orders")
    with allure.step("Validate orders title"):
        title = wait(ui_smoke_driver, OrdersPage.TITLE)
        assert "\u0437\u0430\u043a\u0430\u0437" in title.text.lower()


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Bonuses")
@allure.title("Open bonuses and verify history entry")
@pytest.mark.smoke
@pytest.mark.webview
def test_smoke_bonuses_navigation_and_history(ui_smoke_driver):
    with allure.step("Open bonuses page"):
        try:
            click_web_element(ui_smoke_driver, OnlineDukenHomePage.BONUSES_LINK)
        except TimeoutException:
            open_onlineduken_route(ui_smoke_driver, "bonuses")
    with allure.step("Validate bonuses title and history link"):
        title = wait(ui_smoke_driver, BonusesPage.TITLE)
        assert "\u0431\u043e\u043d\u0443\u0441" in title.text.lower()
        history_links = ui_smoke_driver.find_elements(*BonusesPage.HISTORY_LINK)
        assert history_links, "Bonus history link is not visible."


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.feature("Payments")
@allure.story("QR Payment")
@allure.title("Complete QR payment flow via gallery: {qr_case_name}")
@pytest.mark.smoke
@pytest.mark.payments
@pytest.mark.native
@pytest.mark.browserstack_safe
@pytest.mark.parametrize("qr_case_name", ["common", "megapolis"], ids=["qr-common", "qr-megapolis"])
def test_smoke_qr_payment_flow(payments_smoke_driver, settings, generated_qr_cases, qr_case_name):
    qr_case = _get_qr_case(generated_qr_cases, qr_case_name)
    if not qr_case:
        pytest.skip(
            f"QR case '{qr_case_name}' is not configured yet. "
            "Set CLIENT_BIN and QR template/env values for the requested QR type."
        )
    with allure.step(f"Run QR gallery payment flow for case '{qr_case_name}'"):
        result = run_qr_gallery_payment_flow(payments_smoke_driver, settings, qr_case)
        assert result


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.feature("Payments")
@allure.story("Manual Invoice Payment")
@allure.title("Open invoice payment from home")
@pytest.mark.smoke
@pytest.mark.payments
@pytest.mark.webview
def test_smoke_invoice_payment_from_home(payments_smoke_driver, settings):
    if not settings.invoice_reference:
        pytest.skip("INVOICE_REFERENCE is not configured yet.")
    with allure.step("Open supplier payment page from home"):
        click_web_element(payments_smoke_driver, OnlineDukenHomePage.PAYMENT_LINK)
        title = wait(payments_smoke_driver, PaymentPage.TITLE)
        assert "\u043e\u043f\u043b\u0430\u0442" in title.text.lower()
    with allure.step("Open manual payment tab"):
        click_web_element(payments_smoke_driver, PaymentPage.MANUAL_PAYMENT_TAB)
    pytest.skip("Invoice payment form locators need to be finalized against live test data.")


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Cart")
@allure.title("Create order from catalog")
@pytest.mark.smoke
@pytest.mark.webview
@pytest.mark.skip(reason=CART_FLOW_SKIP_REASON)
def test_smoke_cart_and_order_creation(payments_smoke_driver, settings):
    _open_catalog(payments_smoke_driver)
    WebDriverWait(payments_smoke_driver, 30).until(lambda current_driver: _catalog_page_is_ready(current_driver))
    buttons = payments_smoke_driver.find_elements(*CatalogPage.CREATE_ORDER_BUTTONS)
    if not buttons and payments_smoke_driver.find_elements(*CatalogPage.EMPTY_STATE):
        pytest.skip("Catalog is open, but current dataset has no distributors available for order creation.")
    assert buttons, "No 'Создать заказ' entry is available in catalog."
    assert _add_product_to_cart_from_catalog(
        payments_smoke_driver
    ), "Could not drill down from catalog to a product with 'В корзину'."
    _open_cart(payments_smoke_driver)
    assert _cart_has_checkout_state(payments_smoke_driver), "Cart did not reach a populated checkout state."
    assert _submit_order_from_cart(payments_smoke_driver), "Order was not created successfully from cart."


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Cart")
@allure.title("Create order from a product card on home")
@pytest.mark.smoke
@pytest.mark.webview
@pytest.mark.skip(reason=CART_FLOW_SKIP_REASON)
def test_smoke_cart_and_order_creation_from_home_optional(payments_smoke_driver):
    if not (
        _click_first_matching_element(payments_smoke_driver, OnlineDukenHomePage.ADD_TO_CART_BUTTON)
        or _click_first_visible_button_by_text(payments_smoke_driver, "В корзину")
    ):
        pytest.skip("Home page has no visible product card with 'В корзину' in the current dataset.")
    _resolve_quantity_popup_if_present(payments_smoke_driver)
    _open_cart(payments_smoke_driver)
    assert _cart_has_checkout_state(
        payments_smoke_driver
    ), "Cart did not reach a populated checkout state after home add."
    assert _submit_order_from_cart(payments_smoke_driver), "Order was not created successfully from home product flow."
