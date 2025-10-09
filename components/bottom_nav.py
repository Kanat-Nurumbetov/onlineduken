from appium.webdriver.common.appiumby import AppiumBy as By
from screens.base_screen import BaseScreen

class BottomNav(BaseScreen):
    def __init__(self, driver, timeout=10):
        super().__init__(driver, timeout)   # берем self.w из BaseScreen

    TAB_HOME     = (By.ACCESSIBILITY_ID, "Главная")
    TAB_CATALOG  = (By.ACCESSIBILITY_ID, "Каталог")
    TAB_QR       = (By.ACCESSIBILITY_ID, "QR")
    TAB_CART     = (By.ACCESSIBILITY_ID, "Корзина")
    TAB_MORE     = (By.ACCESSIBILITY_ID, "Еще")

    def find_tab_by_text(self, text: str):
        self.find_by_text_instant(text)

    _fallbacks = {
        # content-desc может меняться с локалью → используем regex через descriptionMatches
        "Главная": ('-android uiautomator',
                    'new UiSelector().descriptionMatches(".*(Главная|Home).*")'),

        "Каталог": ('-android uiautomator',
                    'new UiSelector().descriptionMatches(".*(Каталог|Catalog).*")'),

        "QR": ('-android uiautomator',
               'new UiSelector().descriptionMatches(".*(QR|Код|Scanner).*")'),

        "Корзина": ('-android uiautomator',
                    'new UiSelector().descriptionMatches(".*(Корзина|Cart).*")'),

        "Еще": ('-android uiautomator',
                'new UiSelector().descriptionMatches(".*(Ещё|Еще|More).*")'),
    }

    def open(self, name: str, timeout: int | None = None):
        """Открыть вкладку по человекочитаемому имени."""
        locator = getattr(self, f"TAB_{name.upper()}", None)

        # 1) основной путь — accessibility id
        if locator:
            element = self.waits.clickable(*locator, timeout=timeout)
            if element:
                element.click()
                return

        # 2) фолбэк: заранее заданная стратегия из словаря
        if self._click_from_map(name):
            return

        # 3) фолбэк по платформе: текст/descriptionContains (Android) или predicate (iOS)
        if self._click_by_text_platform(name):
            return

        # 4) последний шанс: если есть TextFinder на экране/базе
        if self._click_via_textfinder(name, timeout):
            return

        raise AssertionError(f"Не нашли вкладку: {name!r} ни по accessibility id, ни по фолбэкам")

    # ---------- helpers ----------

    def _click_from_map(self, name: str) -> bool:
        strat, query = self._fallbacks.get(name, (None, None))
        if not strat:
            return False
        try:
            self.driver.find_element(strat, query).click()
            return True
        except Exception:
            return False

    def _click_by_text_platform(self, name: str) -> bool:
        plat = (self.driver.capabilities.get("platformName") or "").lower()

        if plat.startswith("android"):
            q = name.replace('"', r'\"')
            # сначала content-desc, потом text
            for uia in (
                f'new UiSelector().descriptionContains("{q}")',
                f'new UiSelector().textContains("{q}")',
            ):
                try:
                    self.driver.find_element("-android uiautomator", uia).click()
                    return True
                except Exception:
                    continue
            return False

        if plat.startswith("ios"):
            p = name.replace("'", "\\'")
            predicate = (
                f"label CONTAINS[c] '{p}' OR "
                f"name CONTAINS[c] '{p}' OR "
                f"value CONTAINS[c] '{p}'"
            )
            try:
                self.driver.find_element("-ios predicate string", predicate).click()
                return True
            except Exception:
                return False

        # неизвестная платформа — ничего не делаем
        return False

    def _click_via_textfinder(self, name: str, timeout: int | None) -> bool:
        # если в BaseScreen ты хранишь TextFinder как self.texts
        finder = getattr(self, "texts", None)
        if not finder:
            return False
        try:
            found = finder.find_anywhere(name, timeout=timeout)
            if found:
                found.click()
                return True
        except Exception:
            pass
        return False
