from __future__ import annotations

import allure
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.flows import click_web_element, open_onlineduken_route
from mobile_automation.pages.web import BonusesPage, CatalogPage, OnlineDukenHomePage, OrdersPage
from tests.smoke._smoke_helpers import catalog_page_is_ready, open_catalog, wait


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
        open_catalog(ui_smoke_driver)
    with allure.step("Validate supplier cards or a valid empty state"):
        WebDriverWait(ui_smoke_driver, 30).until(lambda current_driver: catalog_page_is_ready(current_driver))
        supplier_cards = ui_smoke_driver.find_elements(*CatalogPage.SUPPLIER_CARDS)
        empty_state = ui_smoke_driver.find_elements(*CatalogPage.EMPTY_STATE)
        assert (
            supplier_cards or empty_state or catalog_page_is_ready(ui_smoke_driver)
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
        assert "заказ" in title.text.lower()


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
        assert "бонус" in title.text.lower()
        history_links = ui_smoke_driver.find_elements(*BonusesPage.HISTORY_LINK)
        assert history_links, "Bonus history link is not visible."
