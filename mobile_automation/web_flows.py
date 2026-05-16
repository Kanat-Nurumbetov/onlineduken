from __future__ import annotations

from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile_automation import js as js_snippets


def open_authenticated_onlineduken(driver: WebDriver, auth_url: str, timeout: int = 30) -> None:
    driver.get(auth_url)
    wait_for_customer_frontend(driver, timeout=timeout)
    choose_first_store_if_present(driver)


def wait_for_customer_frontend(driver: WebDriver, timeout: int = 30) -> None:
    WebDriverWait(driver, timeout).until(lambda current_driver: "/web/customer-frontend/" in current_driver.current_url)


def current_base_url(driver: WebDriver, fallback: str) -> str:
    current_url = driver.current_url
    route_marker = "/web/customer-frontend/"
    if route_marker in current_url:
        return current_url.split(route_marker, 1)[0] + route_marker

    parsed = urlparse(fallback)
    if parsed.scheme and parsed.netloc:
        return fallback.rstrip("/") + "/"
    return "https://b2b.test.onlinebank.kz/web/customer-frontend/"


def open_route(driver: WebDriver, route_suffix: str, fallback_base_url: str, timeout: int = 30) -> None:
    base_url = current_base_url(driver, fallback_base_url)
    target_url = base_url + route_suffix.lstrip("/")
    driver.get(target_url)
    wait_for_customer_frontend(driver, timeout=timeout)
    choose_first_store_if_present(driver)


def click_element(driver: WebDriver, locator: tuple[str, str], timeout: int = 30):
    element = WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)
    return element


def main_text(driver: WebDriver) -> str:
    return (driver.execute_script(js_snippets.load("main_content_text")) or "").strip()


def choose_first_store_if_present(driver: WebDriver) -> bool:
    clicked = driver.execute_script(js_snippets.load("select_store_web_overlay"))
    if not clicked:
        return False

    try:
        WebDriverWait(driver, 10).until(
            lambda current_driver: not current_driver.execute_script(js_snippets.load("store_overlay_visible"))
        )
    except TimeoutException:
        return False
    return True
