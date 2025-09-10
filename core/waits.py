from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Waits:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    def el_visible(self, by, value):
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                EC.visibility_of_element_located((by, value))
            )
        except TimeoutException or NoSuchElementException:
            return False

    def presents_of_el(self, by, value):
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException or NoSuchElementException:
            return False

    def el_clickable(self, by, value):
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            return False

    def el_gone(self, by, value, timeout=None) -> bool:
        t = timeout or self.timeout
        try:
            WebDriverWait(self.driver, t).until(EC.invisibility_of_element_located((by, value)))
            return True
        except TimeoutException:
            return False


