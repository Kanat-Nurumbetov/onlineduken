from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

# from conftest import driver
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

    def find_by_text_fast(self, text: str, exact_match: bool = False, timeout: int = None) -> Optional[WebElement]:
        """
        Быстрый поиск элемента по тексту для Appium (Android/iOS).
        Использует прямой поиск без WebDriverWait для ускорения.

        Args:
            text: текст для поиска
            exact_match: True для точного совпадения, False для частичного (по умолчанию False)
            timeout: таймаут ожидания в секундах (по умолчанию self.timeout)

        Returns:
            WebElement или None
        """
        import time

        wait_time = timeout if timeout is not None else self.timeout
        platform = (self.driver.capabilities.get("platformName") or "").lower()
        deadline = time.time() + wait_time
        poll_interval = 0.3  # Быстрый опрос каждые 300мс

        # Временно убираем implicit wait для ускорения
        original_implicit = self._get_implicit_wait()
        self.driver.implicitly_wait(0)

        try:
            if platform.startswith("android"):
                # Для Android используем UiSelector
                q = text.replace('"', r'\"')

                if exact_match:
                    ui_selector = f'new UiSelector().text("{q}")'
                else:
                    ui_selector = f'new UiSelector().textContains("{q}")'

                # Быстрый поиск с повторами
                while time.time() < deadline:
                    try:
                        elements = self.driver.find_elements("-android uiautomator", ui_selector)
                        if elements:
                            return elements[0]
                    except Exception:
                        pass
                    time.sleep(poll_interval)

                return None

            elif platform.startswith("ios"):
                # Для iOS используем предикаты
                p = text.replace("'", "\\'")

                if exact_match:
                    predicate = f"label == '{p}' OR name == '{p}' OR value == '{p}'"
                else:
                    predicate = f"label CONTAINS[c] '{p}' OR name CONTAINS[c] '{p}' OR value CONTAINS[c] '{p}'"

                # Быстрый поиск с повторами
                while time.time() < deadline:
                    try:
                        elements = self.driver.find_elements("-ios predicate string", predicate)
                        if elements:
                            return elements[0]
                    except Exception:
                        pass
                    time.sleep(poll_interval)

                return None

            else:
                # Fallback для WebView или других платформ
                if exact_match:
                    xpath = f"//*[text()='{text}']"
                else:
                    xpath = f"//*[contains(text(), '{text}')]"

                wait = WebDriverWait(self.driver, wait_time)
                return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

        except Exception as e:
            print(f"⚠️ Элемент с текстом '{text}' не найден: {e}")
            return None
        finally:
            # Восстанавливаем implicit wait
            self.driver.implicitly_wait(original_implicit)

    def find_by_text_instant(self, text: str, exact_match: bool = False) -> Optional[WebElement]:
        """
        Мгновенный поиск без ожидания (0 таймаут).
        Используйте когда уверены что элемент уже на экране.

        Args:
            text: текст для поиска
            exact_match: точное или частичное совпадение

        Returns:
            WebElement или None
        """
        platform = (self.driver.capabilities.get("platformName") or "").lower()

        # Временно убираем implicit wait
        original_implicit = self._get_implicit_wait()
        self.driver.implicitly_wait(0)

        try:
            if platform.startswith("android"):
                q = text.replace('"', r'\"')
                ui_selector = f'new UiSelector().textContains("{q}")' if not exact_match else f'new UiSelector().text("{q}")'

                elements = self.driver.find_elements("-android uiautomator", ui_selector)
                return elements[0] if elements else None

            elif platform.startswith("ios"):
                p = text.replace("'", "\\'")
                if exact_match:
                    predicate = f"label == '{p}' OR name == '{p}' OR value == '{p}'"
                else:
                    predicate = f"label CONTAINS[c] '{p}' OR name CONTAINS[c] '{p}' OR value CONTAINS[c] '{p}'"

                elements = self.driver.find_elements("-ios predicate string", predicate)
                return elements[0] if elements else None

            return None

        except Exception:
            return None
        finally:
            self.driver.implicitly_wait(original_implicit)

    def find_and_click_by_text(self, text: str, exact_match: bool = False, timeout: int = None) -> bool:
        """
        Найти элемент по тексту и сразу кликнуть с проверкой.

        Args:
            text: текст для поиска
            exact_match: точное или частичное совпадение
            timeout: таймаут ожидания

        Returns:
            bool - успешность операции
        """
        element = self.find_by_text_fast(text, exact_match, timeout)
        if element:
            element.click()
            return True
        else:
            print(f"⚠️ Элемент с текстом '{text}' не найден")
            return False

    def _get_implicit_wait(self) -> float:
        """Получить текущий implicit wait в секундах."""
        try:
            settings = self.driver.get_settings()
            implicit_ms = settings.get("implicitWaitMs", 0)
            return implicit_ms / 1000.0
        except Exception:
            return 0.0
