from __future__ import annotations

from selenium import webdriver

from mobile_automation.config import Settings


def build_web_driver(settings: Settings) -> webdriver.Chrome:
    if settings.web_browser != "chrome":
        raise ValueError(
            f"Unsupported WEB_BROWSER='{settings.web_browser}'. "
            "Only 'chrome' is currently implemented for the OnlineDuken web suite."
        )

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
