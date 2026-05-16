from __future__ import annotations

import allure
import pytest
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.flows import click_web_element
from mobile_automation.pages.web import CatalogPage, OnlineDukenHomePage, PaymentPage
from tests.smoke._smoke_helpers import (
    CART_FLOW_SKIP_REASON,
    add_product_to_cart_from_catalog,
    cart_has_checkout_state,
    catalog_page_is_ready,
    click_first_matching_element,
    click_first_visible_button_by_text,
    open_cart,
    open_catalog,
    resolve_quantity_popup_if_present,
    submit_order_from_cart,
    wait,
)


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
        assert "оплат" in title.text.lower()
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
    open_catalog(payments_smoke_driver)
    WebDriverWait(payments_smoke_driver, 30).until(lambda current_driver: catalog_page_is_ready(current_driver))
    buttons = payments_smoke_driver.find_elements(*CatalogPage.CREATE_ORDER_BUTTONS)
    if not buttons and payments_smoke_driver.find_elements(*CatalogPage.EMPTY_STATE):
        pytest.skip("Catalog is open, but current dataset has no distributors available for order creation.")
    assert buttons, "No 'Создать заказ' entry is available in catalog."
    assert add_product_to_cart_from_catalog(
        payments_smoke_driver
    ), "Could not drill down from catalog to a product with 'В корзину'."
    open_cart(payments_smoke_driver)
    assert cart_has_checkout_state(payments_smoke_driver), "Cart did not reach a populated checkout state."
    assert submit_order_from_cart(payments_smoke_driver), "Order was not created successfully from cart."


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.story("Cart")
@allure.title("Create order from a product card on home")
@pytest.mark.smoke
@pytest.mark.webview
@pytest.mark.skip(reason=CART_FLOW_SKIP_REASON)
def test_smoke_cart_and_order_creation_from_home_optional(payments_smoke_driver):
    if not (
        click_first_matching_element(payments_smoke_driver, OnlineDukenHomePage.ADD_TO_CART_BUTTON)
        or click_first_visible_button_by_text(payments_smoke_driver, "В корзину")
    ):
        pytest.skip("Home page has no visible product card with 'В корзину' in the current dataset.")
    resolve_quantity_popup_if_present(payments_smoke_driver)
    open_cart(payments_smoke_driver)
    assert cart_has_checkout_state(
        payments_smoke_driver
    ), "Cart did not reach a populated checkout state after home add."
    assert submit_order_from_cart(payments_smoke_driver), "Order was not created successfully from home product flow."
