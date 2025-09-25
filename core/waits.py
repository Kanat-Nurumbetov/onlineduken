from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Waits:
    def __init__(self, driver, timeout=10, poll=0.5):
        self.driver = driver
        self.timeout = timeout
        self.poll = poll

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
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t, poll_frequency=self.poll)\
               .until(EC.element_to_be_clickable((by, value)))

    def el_gone(self, value, timeout=None) -> bool:
        """Ждёт, пока найденный Found исчезнет (stale/invisible) с учётом контекста."""
        t = timeout or self.timeout
        d = found.driver
        orig = getattr(d, "current_context", "NATIVE_APP")
        try:
            if orig != found.context:
                d.switch_to.context(found.context)

            # 1) стал "протухшим" (частый случай при перерисовке)
            try:
                WebDriverWait(d, t, poll_frequency=self.poll).until(EC.staleness_of(found.element))
                return True
            except TimeoutException:
                pass

            # 2) невидим (если узел жив, но скрыли)
            try:
                WebDriverWait(d, t, poll_frequency=self.poll).until(
                    lambda _ : not found.element.is_displayed()
                )
                return True
            except Exception:
                return False
        finally:
            if getattr(d, "current_context", None) != orig:
                d.switch_to.context(orig)


