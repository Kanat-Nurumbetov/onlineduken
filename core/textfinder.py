from typing import Optional
from dataclasses import dataclass
import time
import logging
from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

# Настройка логирования
logger = logging.getLogger(__name__)


@dataclass
class Found:
    element: WebElement
    context: str  # 'NATIVE_APP' или 'WEBVIEW_*'
    driver: WebDriver

    def __post_init__(self):
        """Валидация входных параметров"""
        if not self.element:
            raise ValueError("element не может быть None")
        if not self.context:
            raise ValueError("context не может быть пустым")
        if not self.driver:
            raise ValueError("driver не может быть None")

    def click(self):
        """
        Умный клик с переключением контекста и fallback стратегиями
        """
        # Проверяем, что драйвер еще активен
        try:
            orig = self.driver.current_context
        except WebDriverException as e:
            if "session" in str(e).lower():
                raise Exception("WebDriver session закрыта") from e
            raise

        context_switched = False

        # Переключаемся в нужный контекст если необходимо
        if orig != self.context:
            try:
                logger.debug(f"Переключение контекста с {orig} на {self.context}")
                self.driver.switch_to.context(self.context)
                context_switched = True
            except WebDriverException as e:
                logger.warning(f"Не удалось переключиться в контекст {self.context}: {e}")
                # Продолжаем выполнение - возможно элемент доступен в текущем контексте

        try:
            # Основная попытка клика
            self.element.click()
            logger.debug("Клик выполнен успешно")

        except (WebDriverException, StaleElementReferenceException) as e:
            logger.debug(f"Основной клик не удался: {e}. Пробуем альтернативные способы")

            # Fallback 1: клик по кликабельному предку
            try:
                anc = self.element.find_element(By.XPATH, "./ancestor::*[@clickable='true'][1]")
                anc.click()
                logger.debug("Клик по предку выполнен успешно")

            except (Exception, StaleElementReferenceException):
                logger.debug("Клик по предку не удался. Пробуем жест по координатам")

                # Fallback 2: жест по центру элемента
                try:
                    r = self.element.rect
                    x = int(r["x"] + r["width"] / 2)
                    y = int(r["y"] + r["height"] / 2)

                    self.driver.execute_script("mobile: clickGesture", {
                        "x": x,
                        "y": y
                    })
                    logger.debug(f"Жест клика выполнен по координатам ({x}, {y})")

                except (StaleElementReferenceException, WebDriverException) as gesture_error:
                    logger.error(f"Все способы клика провалились: {gesture_error}")
                    raise Exception("Элемент стал недоступен или все способы клика провалились") from gesture_error

        finally:
            # Возвращаемся в исходный контекст только если успешно переключились
            if context_switched:
                try:
                    current_context = self.driver.current_context
                    if current_context != orig:
                        logger.debug(f"Возврат в исходный контекст {orig}")
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
        """
        Поиск текста в любом доступном контексте (native app или webview)
        """
        if not text or not text.strip():
            logger.warning("Пустой текст для поиска")
            return None

        t = timeout or self.default_timeout
        deadline = time.monotonic() + t
        platform = (self.driver.capabilities.get("platformName") or "").lower()

        logger.debug(f"Поиск текста '{text}' на платформе {platform}, таймаут: {t}s")

        while time.monotonic() < deadline:
            slice_timeout = min(self.poll, max(0.1, deadline - time.monotonic()))

            # 1) Native поиск
            if platform.startswith("android"):
                el = self._find_native_android(text, slice_timeout)
                if el:
                    logger.debug(f"Найден элемент в native Android: {text}")
                    return Found(el, "NATIVE_APP", self.driver)
            elif platform.startswith("ios"):
                el = self._find_native_ios(text, slice_timeout)
                if el:
                    logger.debug(f"Найден элемент в native iOS: {text}")
                    return Found(el, "NATIVE_APP", self.driver)
            else:
                # Неизвестная платформа - пробуем оба способа
                el = self._find_native_android(text, slice_timeout) or self._find_native_ios(text, slice_timeout)
                if el:
                    logger.debug(f"Найден элемент в native (универсальный): {text}")
                    return Found(el, "NATIVE_APP", self.driver)

            # 2) WebView поиск
            ctx, el = self._find_in_webview(text, slice_timeout)
            if el:
                logger.debug(f"Найден элемент в webview {ctx}: {text}")
                return Found(el, ctx, self.driver)

            time.sleep(self.poll)

        logger.debug(f"Элемент не найден: {text}")
        return None

    def present_anywhere(self, text: str, timeout: Optional[int] = None) -> bool:
        """
        Проверка присутствия текста без сохранения ссылки на элемент
        """
        original_context = None
        try:
            original_context = getattr(self.driver, "current_context", "NATIVE_APP")
            return self.find_anywhere(text, timeout) is not None
        except Exception as e:
            logger.warning(f"Ошибка при проверке присутствия '{text}': {e}")
            return False
        finally:
            # Восстанавливаем исходный контекст
            if original_context:
                try:
                    current = getattr(self.driver, "current_context", None)
                    if current and current != original_context:
                        self.driver.switch_to.context(original_context)
                except Exception as e:
                    logger.warning(f"Не удалось восстановить контекст {original_context}: {e}")

    def _find_native_android(self, text: str, timeout: float):
        """Поиск в нативном Android UI через UiAutomator"""
        end = time.monotonic() + timeout
        q = (text or "").replace('"', r'\"')

        while time.monotonic() < end:
            try:
                # Поиск по description
                els = self.driver.find_elements("-android uiautomator", f'new UiSelector().descriptionContains("{q}")')
                if els:
                    return els[0]

                # Поиск по тексту
                els = self.driver.find_elements("-android uiautomator", f'new UiSelector().textContains("{q}")')
                if els:
                    return els[0]

            except WebDriverException as e:
                logger.debug(f"Ошибка поиска Android native: {e}")

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
                # Поиск по Accessibility ID
                els = self.driver.find_elements(By.ACCESSIBILITY_ID, q)
                if els:
                    return els[0]

                # Поиск по предикату
                els = self.driver.find_elements("-ios predicate string", predicate)
                if els:
                    return els[0]

                # Поиск через Class Chain
                els = self.driver.find_elements("-ios class chain", class_chain)
                if els:
                    return els[0]

            except WebDriverException as e:
                logger.debug(f"Ошибка поиска iOS native: {e}")

            time.sleep(self.poll)
        return None

    def _find_in_webview(self, text: str, timeout: float):
        """Поиск в WebView контекстах"""
        end = time.monotonic() + timeout
        want = (text or "").strip()
        original_context = None

        try:
            original_context = self.driver.current_context
        except WebDriverException:
            pass

        while time.monotonic() < end:
            try:
                contexts = getattr(self.driver, "contexts", ["NATIVE_APP"])
                webviews = [c for c in contexts if c.startswith("WEBVIEW")]

                for ctx in webviews:
                    try:
                        self.driver.switch_to.context(ctx)

                        # Экранируем кавычки для XPath
                        escaped_text = want.replace("'", "''")
                        els = self.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(), '{escaped_text}')]")

                        if els:
                            return ctx, els[0]

                    except WebDriverException as e:
                        logger.debug(f"Ошибка поиска в webview {ctx}: {e}")
                        continue

            except WebDriverException as e:
                logger.debug(f"Ошибка получения webview контекстов: {e}")

            time.sleep(self.poll)

        # Восстанавливаем исходный контекст при неудачном поиске
        if original_context:
            try:
                self.driver.switch_to.context(original_context)
            except WebDriverException:
                pass

        return None, None