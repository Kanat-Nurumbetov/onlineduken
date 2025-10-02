from typing import Optional

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from core import waits
from core.textfinder import TextFinder, Found


class BaseScreen:
    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.waits = waits.Waits(driver, timeout)
        self.text = TextFinder(driver, self.waits)

    def click_element(self, target: tuple | WebElement | Found) -> Optional[WebElement]:
        """Универсальный клик по элементу или локатору."""
        from core.textfinder import Found

        if isinstance(target, Found):
            target.click()
            return target.element

        if hasattr(target, "click") and not isinstance(target, tuple):
            target.click()
            return target

        if isinstance(target, tuple) and len(target) == 2:
            element = self.wait.until(EC.element_to_be_clickable(target))
            element.click()
            return element

        raise ValueError(f"Неподдерживаемый тип для клика: {type(target)}")
