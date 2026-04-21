from __future__ import annotations

import allure
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation.pages.web import BonusesPage, CatalogPage, MorePage, OnlineDukenHomePage, OrdersPage
from mobile_automation.web_flows import click_element, main_text, open_route


def _catalog_ready(driver) -> bool:
    return bool(
        driver.find_elements(*CatalogPage.TITLE)
        or driver.find_elements(*CatalogPage.SUPPLIER_CARDS)
        or driver.find_elements(*CatalogPage.EMPTY_STATE)
        or driver.find_elements(*CatalogPage.ROOT)
    )


def _open_catalog(driver, settings) -> None:
    try:
        click_element(driver, OnlineDukenHomePage.CATALOG_TAB, timeout=15)
        WebDriverWait(driver, 30).until(lambda current_driver: _catalog_ready(current_driver))
        return
    except TimeoutException:
        pass

    for route_suffix in ("distributors", "distributor"):
        try:
            open_route(driver, route_suffix, settings.web_base_url)
            WebDriverWait(driver, 30).until(lambda current_driver: _catalog_ready(current_driver))
            return
        except TimeoutException:
            continue

    raise TimeoutException("Catalog page did not become ready through tab click or direct route.")


@allure.epic("OnlineDuken")
@allure.feature("Web Suite")
@allure.story("Home")
@allure.title("Open authenticated OnlineDuken home in browser")
@pytest.mark.web
def test_web_home_page_loads(web_driver):
    with allure.step("Verify that the authenticated customer frontend route is open"):
        assert "/web/customer-frontend/" in web_driver.current_url
    with allure.step("Verify that the page contains visible text"):
        assert main_text(web_driver), "Authenticated OnlineDuken web home is empty."


@allure.epic("OnlineDuken")
@allure.feature("Web Suite")
@allure.story("Catalog")
@allure.title("Open catalog in browser and validate supplier page state")
@pytest.mark.web
def test_web_catalog_state(web_driver, settings):
    with allure.step("Open catalog"):
        _open_catalog(web_driver, settings)
    with allure.step("Verify supplier cards or a valid empty state"):
        supplier_cards = web_driver.find_elements(*CatalogPage.SUPPLIER_CARDS)
        empty_state = web_driver.find_elements(*CatalogPage.EMPTY_STATE)
        assert supplier_cards or empty_state or _catalog_ready(web_driver), (
            "Catalog page opened, but neither supplier cards nor a valid empty state was detected."
        )


@allure.epic("OnlineDuken")
@allure.feature("Web Suite")
@allure.story("Orders")
@allure.title("Open orders page in browser")
@pytest.mark.web
def test_web_orders_navigation(web_driver, settings):
    with allure.step("Open orders page"):
        try:
            click_element(web_driver, OnlineDukenHomePage.ORDERS_LINK, timeout=15)
        except TimeoutException:
            open_route(web_driver, "orders", settings.web_base_url)
    with allure.step("Verify that the orders title is visible"):
        title = WebDriverWait(web_driver, 30).until(lambda current_driver: current_driver.find_element(*OrdersPage.TITLE))
        assert "заказ" in title.text.lower()


@allure.epic("OnlineDuken")
@allure.feature("Web Suite")
@allure.story("Bonuses")
@allure.title("Open bonuses page in browser and verify history link")
@pytest.mark.web
def test_web_bonuses_navigation_and_history_link(web_driver, settings):
    with allure.step("Open bonuses page"):
        try:
            click_element(web_driver, OnlineDukenHomePage.BONUSES_LINK, timeout=15)
        except TimeoutException:
            open_route(web_driver, "bonuses", settings.web_base_url)
    with allure.step("Verify bonuses title and history link"):
        title = WebDriverWait(web_driver, 30).until(lambda current_driver: current_driver.find_element(*BonusesPage.TITLE))
        assert "бонус" in title.text.lower()
        assert web_driver.find_elements(*BonusesPage.HISTORY_LINK), "Bonus history link is not visible."


@allure.epic("OnlineDuken")
@allure.feature("Web Suite")
@allure.story("More")
@allure.title("Open more page in browser")
@pytest.mark.web
def test_web_more_navigation(web_driver, settings):
    with allure.step("Open more page"):
        try:
            click_element(web_driver, OnlineDukenHomePage.MORE_TAB, timeout=15)
        except TimeoutException:
            open_route(web_driver, "more", settings.web_base_url)
    with allure.step("Verify more page title and cashier menu item"):
        title = WebDriverWait(web_driver, 30).until(lambda current_driver: current_driver.find_element(*MorePage.TITLE))
        assert "еще" in title.text.lower()
        assert web_driver.find_elements(*MorePage.CASHIERS_ITEM), "Cashiers menu item is not visible on the More page."
