from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Waits:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    def el_visible(self, by, value, timeout=None):
        """Возвращает видимый элемент или ``None``."""
        wait_timeout = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, wait_timeout).until(
                EC.visibility_of_element_located((by, value))
            )
        except (TimeoutException, NoSuchElementException):
            return None

    def el_clickable(self, by, value, timeout=None):
        """Возвращает кликабельный элемент или ``None``."""
        wait_timeout = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, wait_timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except (TimeoutException, NoSuchElementException):
            return None

    # публичные обёртки, чтобы вызывать единообразно из экранов/компонентов
    def visible(self, by, value, timeout=None):
        return self.el_visible(by, value, timeout=timeout)

    def clickable(self, by, value, timeout=None):
        return self.el_clickable(by, value, timeout=timeout)

    def el_gone(self, by, value, timeout=None) -> bool:
        t = timeout or self.timeout
        try:
            WebDriverWait(self.driver, t).until(EC.invisibility_of_element_located((by, value)))
            return True
        except TimeoutException:
            return False


