from typing import Optional
from dataclasses import dataclass
import time
from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common import WebDriverException



@dataclass
class Found:
    element: object   # WebElement
    context: str      # 'NATIVE_APP' или 'WEBVIEW_*'
    driver: object         # WebDriver

    def click(self):
        orig = self.driver.current_context
        if orig != self.context:
            self.driver.switch_to.context(self.context)
        try:
            self.element.click()
        except WebDriverException:
            # клик по предку
            try:
                anc = self.element.find_element(By.XPATH, "./ancestor::*[@clickable='true'][1]")
                anc.click()
            except Exception:
                # жест по центру
                r = self.element.rect
                self.driver.execute_script("mobile: clickGesture", {
                    "x": int(r["x"] + r["width"] / 2),
                    "y": int(r["y"] + r["height"] / 2)
                })
        finally:
            if self.driver.current_context != orig:
                self.driver.switch_to.context(orig)

class TextFinder:
    def __init__(self, driver, waits, default_timeout: int = 10, poll: float = 0.5):
        self.driver = driver
        self.waits = waits
        self.default_timeout = default_timeout
        self.poll = poll

    def find_anywhere(self, text: str, timeout: Optional[int] = None) -> Optional[Found]:
        t = timeout or self.default_timeout
        deadline = time.monotonic() + t
        platform = (self.driver.capabilities.get("platformName") or "").lower()

        while time.monotonic() < deadline:
            slice_timeout = min(self.poll, max(0.1, deadline - time.monotonic()))

            # 1) Native
            if platform.startswith("android"):
                el = self._find_native_android(text, slice_timeout)
                if el: return Found(el, "NATIVE_APP", self.driver)
            elif platform.startswith("ios"):
                el = self._find_native_ios(text, slice_timeout)
                if el: return Found(el, "NATIVE_APP", self.driver)
            else:
                el = self._find_native_android(text, slice_timeout) or self._find_native_ios(text, slice_timeout)
                if el: return Found(el, "NATIVE_APP")

            # 2) WebView (вернёт (ctx, el) и оставит нас в этом ctx)
            ctx, el = self._find_in_webview(text, slice_timeout)
            if el: return Found(el, ctx, self.driver)

            time.sleep(self.poll)

        return None

    def present_anywhere(self, text: str, timeout: Optional[int] = None) -> bool:
        original = getattr(self.driver, "current_context", "NATIVE_APP")
        try:
            return self.find_anywhere(text, timeout) is not None
        finally:
            try:
                if getattr(self.driver, "current_context", None) != original:
                    self.driver.switch_to.context(original)
            except Exception:
                pass

    def _find_native_android(self, text: str, timeout: float):
        end = time.monotonic() + timeout
        q = (text or "").replace('"', r'\"')
        while time.monotonic() < end:
            els = self.driver.find_elements("-android uiautomator", f'new UiSelector().descriptionContains("{q}")')
            if els: return els[0]
            els = self.driver.find_elements("-android uiautomator", f'new UiSelector().textContains("{q}")')
            if els: return els[0]
            time.sleep(self.poll)
        return None

    def _find_native_ios(self, text: str, timeout: float):
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
            els = self.driver.find_elements(By.ACCESSIBILITY_ID, q)
            if els:
                return els[0]

            els = self.driver.find_elements("-ios predicate string", predicate)
            if els:
                return els[0]

            # 3) опциональный fallback через Class Chain (иногда быстрее на больших деревьях)
            els = self.driver.find_elements("-ios class chain", class_chain)
            if els:
                return els[0]

            time.sleep(self.poll)

        return None

    # -------- WEBVIEW ----------
    def _find_in_webview(self, text: str, timeout: float):
        end = time.monotonic() + timeout
        want = (text or "").strip()
        while time.monotonic() < end:
            webviews = [c for c in getattr(self.driver, "contexts", ["NATIVE_APP"]) if c.startswith("WEBVIEW")]
            for ctx in webviews:
                try:
                    self.driver.switch_to.context(ctx)
                    els = self.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(), '{want}')]")
                    if els:
                        return ctx, els[0]
                except Exception:
                    continue
            time.sleep(self.poll)
        return None, None