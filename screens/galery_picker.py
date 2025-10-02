# screens/picker.py
from __future__ import annotations

import time
from contextlib import suppress
from typing import Optional, List, Tuple

from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
)
from screens.base_screen import BaseScreen


class PickerScreen(BaseScreen):
    """
    Минимальный экран системного пикера изображений для Android.
    Поддержка:
      - System Photo Picker: com.google.android.providers.media.module
      - DocumentsUI: com.android.documentsui / com.google.android.documentsui
      - (фолбэк) Google Photos: com.google.android.apps.photos
    """

    # пакеты провайдеров
    MEDIA_MODULE_PKG = "com.google.android.providers.media.module"
    DOCSUI_PACKAGES  = ("com.android.documentsui", "com.google.android.documentsui")
    PHOTOS_PACKAGE   = "com.google.android.apps.photos"

    # якорные id (разные провайдеры)
    MM_THUMB_ID      = "id/icon_thumbnail"                # превью в media.module
    DOCS_LIST_IDS    = ("id/dir_list", "id/list", "id/container_directory_list")
    PHOTOS_GRID_IDS  = ("id/recycler_view", "id/photos_grid", "id/photos_view")

    # подтверждение выбора (если требуется)
    MM_CONFIRM_IDS   = ("id/confirm_button",)
    DOCS_CONFIRM_IDS = ("id/action_menu_done", "id/done")
    PHOTOS_CONFIRM_IDS = ("id/done_button", "id/confirm_button")

    def __init__(self, driver, timeout: int = 10):
        super().__init__(driver, timeout)
        self._provider: Optional[str] = None  # 'mediamodule' | 'documentsui' | 'photos' | None

    # ---------- публичные методы ----------

    def wait_loaded(self, timeout: Optional[int] = None) -> bool:
        """Ждём, что открылся какой-то из известных пикеров."""
        t = timeout or self.waits.timeout
        end = time.monotonic() + t
        while time.monotonic() < end:
            pkg = self.driver.current_package or ""

            if pkg.startswith(self.MEDIA_MODULE_PKG):
                self._provider = "mediamodule"
                # убеждаемся, что появились миниатюры или контейнер
                if self._has_any(By.ID, self._rid(pkg, self.MM_THUMB_ID)) or self._has_any(
                    By.ID, self._rid(pkg, "id/picker_tab_recyclerview")
                ):
                    return True

            elif any(pkg.startswith(p) for p in self.DOCSUI_PACKAGES):
                self._provider = "documentsui"
                if self._find_docs_container():
                    return True

            elif pkg.startswith(self.PHOTOS_PACKAGE):
                self._provider = "photos"
                if self._find_photos_container():
                    return True

            else:
                # универсальный фолбэк: появились ли кликабельные элементы
                if self._list_items(limit=1):
                    return True

            time.sleep(0.2)

        return False

    def select_first_recent(self, timeout: Optional[int] = None) -> bool:
        """Выбрать первый элемент в «Недавних» (или первом видимом контейнере)."""
        if not self._provider:
            self.wait_loaded(timeout=timeout)

        pkg = self.driver.current_package or ""
        prov = self._provider

        if prov == "mediamodule":
            # превью не кликабельно → кликаем кликабельного предка или тапаем по центру
            thumbs = self.driver.find_elements(By.ID, self._rid(pkg, self.MM_THUMB_ID))
            if thumbs:
                thumb = thumbs[0]
                with suppress(NoSuchElementException, WebDriverException, StaleElementReferenceException):
                    parent = thumb.find_element(By.XPATH, "./ancestor::*[@clickable='true'][1]")
                    parent.click()
                    return True
                return self._tap_center(thumb)

        # DocumentsUI / Photos / неизвестный → кликаем первый кликабельный элемент в контейнере
        items = self._list_items(limit=6)
        if not items:
            self._scroll_list_down()
            items = self._list_items(limit=6)
        if items:
            with suppress(WebDriverException, StaleElementReferenceException):
                items[0].click()
                return True
        return False

    def confirm_if_needed(self) -> None:
        """Нажать подтверждение, если у провайдера есть такая кнопка."""
        pkg = self.driver.current_package or ""
        prov = self._provider

        ids: Tuple[str, ...] = ()
        if prov == "mediamodule":
            ids = tuple(self._rid(pkg, i) for i in self.MM_CONFIRM_IDS)
        elif prov == "documentsui":
            ids = tuple(self._rid(pkg, i) for i in self.DOCS_CONFIRM_IDS)
        elif prov == "photos":
            ids = tuple(self._rid(pkg, i) for i in self.PHOTOS_CONFIRM_IDS)

        for rid in ids:
            with suppress(WebDriverException, NoSuchElementException):
                button = self.waits.clickable(By.ID, rid, timeout=2)
                if button:
                    button.click()
                    return
        # многие пикеры подтверждение не требуют — no-op

    def cancel(self) -> None:
        with suppress(WebDriverException):
            self.driver.back()

    # ---------- внутренние помощники ----------

    @staticmethod
    def _rid(pkg: str, short_id: str) -> str:
        return short_id if ":" in short_id else f"{pkg}:{short_id}"

    def _has_any(self, by, value) -> bool:
        with suppress(NoSuchElementException, WebDriverException):
            return len(self.driver.find_elements(by, value)) > 0
        return False

    def _find_docs_container(self):
        pkg = self.driver.current_package or ""
        for sid in self.DOCS_LIST_IDS:
            rid = self._rid(pkg, sid)
            if self._has_any(By.ID, rid):
                return By.ID, rid
        return None

    def _find_photos_container(self):
        pkg = self.driver.current_package or ""
        for sid in self.PHOTOS_GRID_IDS:
            rid = self._rid(pkg, sid)
            if self._has_any(By.ID, rid):
                return By.ID, rid
        return None

    def _list_container_locator(self) -> Optional[Tuple[str, str]]:
        if self._provider == "documentsui":
            return self._find_docs_container()
        if self._provider == "photos":
            return self._find_photos_container()
        if self._provider == "mediamodule":
            # у системного пикера контейнеры разные; кликаем по превью/предку, поэтому None ок
            return None
        return None

    def _list_items(self, limit: int = 20) -> List:
        loc = self._list_container_locator()
        if loc:
            by, rid = loc
            with suppress(WebDriverException, NoSuchElementException):
                root = self.driver.find_element(by, rid)
                items = root.find_elements(By.XPATH, ".//*[@clickable='true' or @focusable='true']")
                if not items:
                    items = root.find_elements(By.XPATH, "./*")
                return items[:limit]
        # фолбэк: любые кликабельные на экране
        with suppress(WebDriverException):
            return self.driver.find_elements(By.XPATH, "//*[@clickable='true' or @focusable='true']")[:limit]
        return []

    def _scroll_list_down(self) -> bool:
        """Короткий скролл вниз в пределах контейнера (или по экрану)."""
        loc = self._list_container_locator()
        if not loc:
            # скролл по экрану как фолбэк
            size = self.driver.get_window_size()
            x = int(size["width"] * 0.5)
            start_y = int(size["height"] * 0.75)
            end_y = int(size["height"] * 0.35)
            with suppress(WebDriverException):
                self.driver.swipe(x, start_y, x, end_y, 300)
                return True
            return False

        by, rid = loc
        container = self.driver.find_element(by, rid)
        rect = container.rect
        with suppress(WebDriverException):
            self.driver.execute_script(
                "mobile: scrollGesture",
                {
                    "left": rect["x"] + 8,
                    "top": rect["y"] + 8,
                    "width": max(16, rect["width"] - 16),
                    "height": max(16, rect["height"] - 16),
                    "direction": "down",
                    "percent": 0.8,
                },
            )
            return True
        return False

    def _tap_center(self, el) -> bool:
        """Тап по центру элемента как последний фолбэк."""
        with suppress(WebDriverException):
            r = el.rect
            self.driver.execute_script(
                "mobile: clickGesture",
                {"x": int(r["x"] + r["width"] / 2), "y": int(r["y"] + r["height"] / 2)}
            )
            return True
        return False
