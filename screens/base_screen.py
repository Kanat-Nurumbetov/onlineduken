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

        def safe_text_click(self, text: str, timeout: int = 10) -> bool:
            """
            Безопасный поиск и клик по тексту
            Возвращает True если клик выполнен, False если элемент не найден
            """
            element = self.text.find_anywhere(text, timeout=timeout)
            if element:
                element.click()
                return True
            else:
                print(f"Элемент с текстом '{text}' не найден")
                return False

        def require_text_click(self, text: str, timeout: int = 10):
            """
            Поиск и клик по тексту с обязательным выбрасыванием исключения при неудаче
            """
            element = self.text.find_anywhere(text, timeout=timeout)
            if element:
                element.click()
            else:
                raise Exception(f"Обязательный элемент с текстом '{text}' не найден на экране в течение {timeout}с")
