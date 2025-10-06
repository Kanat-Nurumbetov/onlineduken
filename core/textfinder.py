from contextlib import suppress, contextmanager
from dataclasses import dataclass
import time
import logging
from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException, NoSuchElementException
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from appium.webdriver.webelement import WebElement as AppiumWebElement
from typing import Optional

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class Found:
    element: AppiumWebElement
    context: str
    driver: AppiumWebDriver

    def __post_init__(self):
        """Валидация входных параметров"""
        if not self.element:
            raise ValueError("element не может быть None")
        if not self.context:
            raise ValueError("context не может быть пустым")
        if not self.driver:
            raise ValueError("driver не может быть None")

    def click(self):
        """Умный клик с переключением контекста и fallback стратегиями"""
        try:
            orig = self.driver.current_context
        except WebDriverException as e:
            if "session" in str(e).lower():
                raise Exception("WebDriver session закрыта") from e
            raise

        context_switched = False

        if orig != self.context:
            try:
                self.driver.switch_to.context(self.context)
                context_switched = True
            except WebDriverException as e:
                logger.warning(f"Не удалось переключиться в контекст {self.context}: {e}")

        try:
            self.element.click()

        except (WebDriverException, StaleElementReferenceException):
            # Fallback 1: клик по кликабельному предку
            try:
                anc = self.element.find_element(By.XPATH, "./ancestor::*[@clickable='true'][1]")
                anc.click()

            except (Exception, StaleElementReferenceException):
                # Fallback 2: жест по центру элемента
                try:
                    r = self.element.rect
                    x = int(r["x"] + r["width"] / 2)
                    y = int(r["y"] + r["height"] / 2)

                    self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})

                except (StaleElementReferenceException, WebDriverException) as gesture_error:
                    logger.error(f"Все способы клика провалились: {gesture_error}")
                    raise Exception("Элемент стал недоступен или все способы клика провалились") from gesture_error

        finally:
            if context_switched:
                try:
                    current_context = self.driver.current_context
                    if current_context != orig:
                        self.driver.switch_to.context(orig)
                except WebDriverException as e:
                    logger.warning(f"Не удалось вернуться в исходный контекст {orig}: {e}")


class TextFinder:
    def __init__(self, driver, waits, default_timeout: int = 10, poll: float = 0.5):
        self.driver = driver
        self.waits = waits
        self.default_timeout = default_timeout
        self.poll = poll

    def find_anywhere(self, text: str, timeout: Optional[int] = None) -> Optional[Found]:
        """Поиск текста в любом доступном контексте (native app или webview)"""
        if not text or not text.strip():
            logger.warning("Пустой текст для поиска")
            return None

        t = timeout or self.default_timeout
        deadline = time.monotonic() + t
        platform = (self.driver.capabilities.get("platformName") or "").lower()

        try:
            original_context = getattr(self.driver, "current_context", "NATIVE_APP")
        except WebDriverException:
            original_context = "NATIVE_APP"

        while time.monotonic() < deadline:
            slice_timeout = min(self.poll, max(0.1, deadline - time.monotonic()))

            # 1) Native поиск
            if platform.startswith("android"):
                el = self._find_native_android(text, slice_timeout)
                if el:
                    return Found(el, "NATIVE_APP", self.driver)
            elif platform.startswith("ios"):
                el = self._find_native_ios(text, slice_timeout)
                if el:
                    return Found(el, "NATIVE_APP", self.driver)
            else:
                el = self._find_native_android(text, slice_timeout) or self._find_native_ios(text, slice_timeout)
                if el:
                    return Found(el, "NATIVE_APP", self.driver)

            # 2) WebView поиск
            ctx, el = self._find_in_webview(text, slice_timeout, original_context=original_context)
            if el:
                return Found(el, ctx, self.driver)

            time.sleep(self.poll)

        logger.warning(f"Элемент не найден за {t}s: '{text}'")
        return None

    def find_all_anywhere(self, text: str, timeout=10):
        """
        Поиск всех элементов с указанным текстом в NATIVE_APP и всех WEBVIEW контекстах.

        Args:
            text: текст для поиска
            timeout: таймаут ожидания

        Returns:
            Список Found объектов или пустой список
        """
        if not text or not text.strip():
            logger.warning("Пустой текст для поиска")
            return []

        end = time.time() + timeout
        found_elements = []
        platform = (self.driver.capabilities.get("platformName") or "").lower()

        try:
            original_context = getattr(self.driver, "current_context", "NATIVE_APP")
        except WebDriverException:
            original_context = "NATIVE_APP"

        while time.time() < end:
            # Получаем все доступные контексты
            try:
                contexts = list(self.driver.contexts)
            except WebDriverException:
                contexts = ["NATIVE_APP"]

            for ctx in contexts:
                try:
                    self.driver.switch_to.context(ctx)
                except WebDriverException as e:
                    logger.warning(f"Не удалось переключиться в контекст {ctx}: {e}")
                    continue

                # Ищем элементы в зависимости от контекста
                try:
                    if ctx == "NATIVE_APP":
                        # Для Android
                        if platform.startswith("android"):
                            q = text.replace('"', r'\"')
                            ui = f'new UiSelector().textContains("{q}")'
                            elements = self.driver.find_elements("-android uiautomator", ui)
                        # Для iOS
                        elif platform.startswith("ios"):
                            p = text.replace("'", "\\'")
                            predicate = f"label CONTAINS[c] '{p}' OR name CONTAINS[c] '{p}' OR value CONTAINS[c] '{p}'"
                            elements = self.driver.find_elements("-ios predicate string", predicate)
                        else:
                            elements = []
                    else:
                        # WebView контекст
                        lit = self._xpath_literal(text)
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(), {lit})]")

                    # Добавляем только видимые элементы
                    for element in elements:
                        try:
                            if element.is_displayed():
                                found_elements.append(Found(element, ctx, self.driver))
                        except (StaleElementReferenceException, WebDriverException):
                            continue

                except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
                    logger.debug(f"Ошибка при поиске в контексте {ctx}: {e}")
                    continue

            # Если нашли элементы, возвращаем их
            if found_elements:
                # Восстанавливаем оригинальный контекст
                try:
                    if self.driver.current_context != original_context:
                        self.driver.switch_to.context(original_context)
                except WebDriverException:
                    pass
                return found_elements

            time.sleep(self.poll)

        # Восстанавливаем оригинальный контекст
        try:
            if self.driver.current_context != original_context:
                self.driver.switch_to.context(original_context)
        except WebDriverException:
            pass

        return []

    def present_anywhere(self, text: str, timeout: Optional[int] = None) -> bool:
        """Проверка присутствия текста без сохранения ссылки на элемент"""
        original_context = None
        try:
            original_context = getattr(self.driver, "current_context", "NATIVE_APP")
            return self.find_anywhere(text, timeout) is not None
        except Exception as e:
            logger.warning(f"Ошибка при проверке присутствия '{text}': {e}")
            return False
        finally:
            if original_context:
                try:
                    current = getattr(self.driver, "current_context", None)
                    if current and current != original_context:
                        self.driver.switch_to.context(original_context)
                except Exception as e:
                    logger.warning(f"Не удалось восстановить контекст {original_context}: {e}")

    def _find_native_android(self, text: str, timeout: float):
        end = time.monotonic() + timeout
        q = (text or "").replace('"', r'\"')

        with self._temporary_implicit_wait(0):
            while time.monotonic() < end:
                try:
                    # Объединённый поиск
                    ui = f'new UiSelector().textContains("{q}")'
                    els = self.driver.find_elements("-android uiautomator", ui)
                    if els:
                        return els[0]

                    # Запасной регистронезависимый поиск
                    ui = f'new UiSelector().textMatches("(?i).*{q}.*")'
                    els = self.driver.find_elements("-android uiautomator", ui)
                    if els:
                        return els[0]

                except WebDriverException:
                    pass
                time.sleep(self.poll)
        return None

    def _find_native_ios(self, text: str, timeout: float):
        """Поиск в нативном iOS UI через предикаты и цепочки классов"""
        end = time.monotonic() + timeout
        q = (text or "").strip()
        if not q:
            return None

        p = q.replace("'", "\\'")
        predicate = (
            f"label CONTAINS[c] '{p}' OR "
            f"name CONTAINS[c] '{p}'  OR "
            f"value CONTAINS[c] '{p}'"
        )
        class_chain = f"**/XCUIElementTypeAny[`{predicate}`]"

        while time.monotonic() < end:
            try:
                els = self.driver.find_elements(By.ACCESSIBILITY_ID, q)
                if els:
                    return els[0]

                els = self.driver.find_elements("-ios predicate string", predicate)
                if els:
                    return els[0]

                els = self.driver.find_elements("-ios class chain", class_chain)
                if els:
                    return els[0]

            except WebDriverException:
                pass

            time.sleep(self.poll)
        return None

    @contextmanager
    def _temporary_implicit_wait(self, seconds: float):
        """Временно меняет implicit wait, чтобы обходные поиски не зависали на секунды."""
        original_ms = None
        driver = self.driver
        try:
            original_ms = driver.get_settings().get("implicitWaitMs")
        except Exception:
            pass

        try:
            driver.implicitly_wait(seconds)
        except Exception:
            yield
        else:
            try:
                yield
            finally:
                restore = (original_ms or 0) / 1000 if original_ms is not None else 0
                with suppress(Exception):
                    driver.implicitly_wait(restore)

    @staticmethod
    def _xpath_literal(s: str) -> str:
        if "'" not in s:
            return f"'{s}'"
        if '"' not in s:
            return f'"{s}"'
        parts = s.split("'")
        return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

    def _find_in_webview(self, text: str, timeout: float, original_context: str | None = None) -> tuple[
        Optional[str], Optional[AppiumWebElement]]:

        driver = self.driver
        orig = getattr(driver, "current_context", "NATIVE_APP")
        deadline = time.monotonic() + timeout
        q = text.strip()

        try:
            contexts = list(driver.contexts)

            for ctx in contexts:
                if not str(ctx).startswith("WEBVIEW"):
                    continue

                driver.switch_to.context(ctx)

                try:
                    inner = driver.execute_script("return document.body?.innerText || '';")
                    if q.casefold() in inner.casefold():
                        lit = self._xpath_literal(q)
                        els = driver.find_elements(By.XPATH, f"//*[contains(normalize-space(), {lit})]")
                        if els:
                            found_ctx = driver.current_context
                            driver.switch_to.context(orig)
                            return found_ctx, els[0]
                except Exception:
                    pass

                if time.monotonic() > deadline:
                    break

            return None, None

        finally:
            if getattr(driver, "current_context", None) != orig:
                with suppress(Exception):
                    driver.switch_to.context(orig)
