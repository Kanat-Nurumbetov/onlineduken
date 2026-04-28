from __future__ import annotations

from appium import webdriver as appium_webdriver
from appium.webdriver.client_config import AppiumClientConfig
from appium.options.android import UiAutomator2Options
from selenium import webdriver
from selenium.webdriver.remote.client_config import ClientConfig

from mobile_automation.config import Settings


def _browserstack_hub_url() -> str:
    return "https://hub-cloud.browserstack.com/wd/hub"


def _browserstack_selenium_client_config(settings: Settings) -> ClientConfig:
    return ClientConfig(
        remote_server_addr=_browserstack_hub_url(),
        username=settings.browserstack_username,
        password=settings.browserstack_access_key,
        timeout=300,
    )


def _browserstack_appium_client_config(settings: Settings) -> AppiumClientConfig:
    return AppiumClientConfig(
        remote_server_addr=_browserstack_hub_url(),
        username=settings.browserstack_username,
        password=settings.browserstack_access_key,
        timeout=300,
    )


def _build_browserstack_mobile_web_driver(settings: Settings, session_name: str):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.set_capability("browserName", "Chrome")
    options.set_capability("appium:newCommandTimeout", 240)
    options.set_capability(
        "bstack:options",
        {
            "deviceName": settings.browserstack_android_device,
            "platformVersion": settings.browserstack_android_os_version,
            "platformName": "android",
            "projectName": settings.browserstack_project_name,
            "buildName": f"{settings.browserstack_build_name}-web",
            "sessionName": session_name,
            "debug": True,
            "networkLogs": True,
            "appiumLogs": True,
            "deviceLogs": True,
        },
    )
    driver = appium_webdriver.Remote(
        command_executor=_browserstack_hub_url(),
        options=options,
        client_config=_browserstack_appium_client_config(settings),
    )
    driver.implicitly_wait(settings.implicit_wait_sec)
    return driver


def _build_browserstack_desktop_web_driver(settings: Settings, session_name: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=ru-RU")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.set_capability("browserName", settings.browserstack_web_browser)
    options.set_capability("browserVersion", settings.browserstack_web_browser_version)
    options.set_capability(
        "bstack:options",
        {
            "os": settings.browserstack_web_os,
            "osVersion": settings.browserstack_web_os_version,
            "projectName": settings.browserstack_project_name,
            "buildName": f"{settings.browserstack_build_name}-web",
            "sessionName": session_name,
            "debug": True,
            "networkLogs": True,
        },
    )
    driver = webdriver.Remote(
        command_executor=_browserstack_hub_url(),
        options=options,
        client_config=_browserstack_selenium_client_config(settings),
    )
    driver.implicitly_wait(settings.implicit_wait_sec)
    return driver


def build_web_driver(settings: Settings, session_name: str = "OnlineDuken web"):
    if settings.web_browser != "chrome":
        raise ValueError(
            f"Unsupported WEB_BROWSER='{settings.web_browser}'. "
            "Only 'chrome' is currently implemented for the OnlineDuken web suite."
        )

    if settings.is_browserstack:
        settings.require(
            ("BROWSERSTACK_USERNAME", settings.browserstack_username),
            ("BROWSERSTACK_ACCESS_KEY", settings.browserstack_access_key),
        )
        if settings.browserstack_web_driver_mode == "desktop":
            return _build_browserstack_desktop_web_driver(settings, session_name)
        return _build_browserstack_mobile_web_driver(settings, session_name)

    options = webdriver.ChromeOptions()
    options.add_argument("--lang=ru-RU")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    if settings.web_headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(settings.implicit_wait_sec)
    return driver
