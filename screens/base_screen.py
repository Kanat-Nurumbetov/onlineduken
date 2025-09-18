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
        # исторический алиас для совместимости с компонентами
        self.texts = self.text

    def click_element(self, target):
        """Приводит аргумент к кликабельному элементу и кликает по нему.

        Поддерживаются локаторы (``(by, value)``), ``WebElement`` и ``TextFinder.Found``.
        Возвращает элемент, по которому удалось кликнуть, иначе ``None``.
        """

        # 1) уже найденный TextFinder.Found
        from core.textfinder import Found  # локальный импорт во избежание циклов

        if isinstance(target, Found):
            try:
                target.click()
                return target.element
            except Exception:
                return None

        # 2) обычный WebElement
        if hasattr(target, "click") and hasattr(target, "is_enabled") and not isinstance(target, tuple):
            try:
                target.click()
                return target
            except Exception:
                return None

        # 3) локатор (By, value)
        if isinstance(target, tuple) and len(target) == 2:
            try:
                element = self.wait.until(EC.element_to_be_clickable(target))
                element.click()
                return element
            except TimeoutException:
                print(f"Элемент не найден {target}")
                return None

        print(f"Неизвестный тип для клика: {type(target)}")
        return None

    def safe_text_click(self, text: str, timeout: int = 10) -> bool:
        """Безопасный поиск и клик по тексту.

        Возвращает ``True`` если клик выполнен, ``False`` если элемент не найден.
        """

        found = self.text.find_anywhere(text, timeout=timeout)
        if found:
            try:
                found.click()
                return True
            except Exception as exc:
                print(f"Не удалось кликнуть по тексту '{text}': {exc}")
                return False

        print(f"Элемент с текстом '{text}' не найден")
        return False

    def require_text_click(self, text: str, timeout: int = 10):
        """Обязательный поиск текста с ошибкой при неудаче."""

        found = self.text.find_anywhere(text, timeout=timeout)
        if not found:
            raise TimeoutException(
                f"Обязательный элемент с текстом '{text}' не найден на экране в течение {timeout}с"
            )
        found.click()
