from appium.webdriver.common.appiumby import AppiumBy as By
from screens.base_screen import BaseScreen

class BottomNav(BaseScreen):
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.w = self.waits(driver, timeout)

    TAB_HOME     = (By.ACCESSIBILITY_ID, "Главная")   # fallback ниже
    TAB_CATALOG  = (By.ACCESSIBILITY_ID, "Каталог")
    TAB_QR       = (By.ACCESSIBILITY_ID, "QR")
    TAB_CART     = (By.ACCESSIBILITY_ID, "Корзина")
    TAB_MORE     = (By.ACCESSIBILITY_ID, "Еще")

    _fallbacks = {
        "Главная": ('-android uiautomator', 'new UiSelector().descriptionContains("Глав")'),
        # добавь при необходимости для остальных
    }

    def open(self, name: str):
        """Открыть вкладку по человекочитаемому имени."""
        locator = getattr(self, f"TAB_{name.upper()}", None)
        if locator:
            try:
                self.w.el_clickable(*locator).click()
            except Exception:
                # fallback: описание частичным совпадением
                strategy, query = self._fallbacks.get(name, (None, None))
                if strategy:
                    self.driver.find_element(strategy, query).click()
                else:
                    raise
        else:
            raise ValueError(f"Неизвестная вкладка: {name}")



