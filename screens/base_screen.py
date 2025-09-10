from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core import waits
from core.textfinder import TextFinder


class BaseScreen:
    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.waits = waits.Waits(driver, timeout)
        self.text = TextFinder(driver, self.waits)

    def click_element(self, locator):
        try:
            return self.wait.until(EC.element_to_be_clickable(locator)).click()
        except TimeoutException:
            print(f"Элемент не найден {locator}")
            return None
