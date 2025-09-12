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
    Экран выбора изображений (галерея/файлы).
    Поддержка:
      - System Photo Picker (Android 13/14): com.google.android.providers.media.module
      - DocumentsUI: com.android.documentsui / com.google.android.documentsui
      - Google Photos (частично)
    """

    # --- тексты кнопок ---
    _ALLOW_TEXTS   = ("Разрешить", "Allow")
    _CANCEL_TEXTS  = ("Отмена", "Cancel")
    _OK_TEXTS      = ("ОК", "OK", "Готово", "Выбрать", "Select", "Done")

    # --- пакеты провайдеров ---
    DOCSUI_PACKAGES     = ("com.android.documentsui", "com.google.android.documentsui")
    PHOTOS_PACKAGE      = "com.google.android.apps.photos"
    MEDIA_MODULE_PKG    = "com.google.android.providers.media.module"  # System Photo Picker

    # --- DocumentsUI локаторы ---
    DOCS_LIST_IDS       = ("id/dir_list", "id/list", "id/container_directory_list")
    DOCS_ITEM_TITLE_ID  = "id/title"        # иногда "id/filename"
    DOCS_CONFIRM_IDS    = ("id/action_menu_done", "id/done")
    DOCS_TOOLBAR_IDS    = ("id/toolbar", "id/action_bar")

    # --- Google Photos локаторы (могут различаться на сборках) ---
    PHOTOS_GRID_IDS     = ("id/recycler_view", "id/photos_grid", "id/photos_view")
    PHOTOS_CONFIRM_IDS  = ("id/done_button", "id/confirm_button")
    PHOTOS_TOOLBAR_IDS  = ("id/action_bar", "id/topbar")

    # --- System Photo Picker (media.module) локаторы ---
    MM_GRID_IDS         = ("id/picker_tab_recyclerview", "id/picker_tab_gridview")
    MM_THUMB_ID         = "id/icon_thumbnail"          # сами превью НЕ кликабельны
    MM_CONFIRM_IDS      = ("id/confirm_button",)       # чаще всего подтверждение не требуется

    def __init__(self, driver, timeout: int = 10):
        super().__init__(driver, timeout)

    # утилита: собрать полный ресурс-id с пакетом
    @staticmethod
    def _rid(pkg: str, short_id: str) -> str:
        return short_id if ":" in short_id else f"{pkg}:{short_id}"

    # определить провайдера по текущему пакету
    def _provider(self) -> str:
        pkg = self.driver.current_package or ""
        if any(pkg.startswith(p) for p in self.DOCSUI_PACKAGES):
            return "documentsui"
        if pkg.startswith(self.MEDIA_MODULE_PKG):
            return "mediamodule"
        if pkg.startswith(self.PHOTOS_PACKAGE):
            return "photos"
        return "unknown"

    # ======== ПУБЛИЧНЫЕ МЕТОДЫ =========

    def wait_loaded(self, timeout: Optional[int] = None) -> bool:
        t = timeout or self.waits.timeout
        end = time.monotonic() + t
        while time.monotonic() < end:
            prov = self._provider()
            pkg = self.driver.current_package or ""
            try:
                if prov == "documentsui":
                    for sid in (*self.DOCS_TOOLBAR_IDS, *self.DOCS_LIST_IDS):
                        if self._is_present(By.ID, self._rid(pkg, sid)):
                            return True
                elif prov in ("mediamodule", "photos"):
                    for sid in (*self.PHOTOS_TOOLBAR_IDS, *self.PHOTOS_GRID_IDS, *self.MM_GRID_IDS):
                        if self._is_present(By.ID, self._rid(pkg, sid)):
                            return True
                # универсальный фолбэк: есть ли вообще кликабельные элементы
                if self._list_items(limit=1):
                    return True
            except WebDriverException:
                pass
            time.sleep(0.2)
        return False

    def grant_permissions_if_needed(self) -> None:
        # системный диалог пермишенов (если всплыл)
        for txt in self._ALLOW_TEXTS:
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element(
                    "-android uiautomator",
                    f'new UiSelector().textContains("{txt}")'
                ).click()
                return
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element(
                    "-android uiautomator",
                    f'new UiSelector().descriptionContains("{txt}")'
                ).click()
                return

    def switch_source(self, tab_text: str) -> bool:
        q = tab_text.strip()
        for uia in (
            f'new UiSelector().textContains("{q}")',
            f'new UiSelector().descriptionContains("{q}")',
        ):
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", uia).click()
                return True
        # фолбэк: TextFinder, если есть
        finder = getattr(self, "texts", None)
        if finder:
            found = finder.find_anywhere(q, timeout=2)
            if found:
                found.element.click()
                return True
        return False

    def select_file_by_name(self, name_substr: str, timeout: Optional[int] = None) -> bool:
        """Выбрать файл, по видимому имени (работает в DocumentsUI). В системном Photo Picker имён нет — используй select_first_recent()."""
        t = timeout or self.waits.timeout
        end = time.monotonic() + t
        q = name_substr.strip().replace('"', r'\"')

        while time.monotonic() < end:
            # 1) быстрый поиск текстом
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", f'new UiSelector().textContains("{q}")').click()
                return True

            # 2) по id названия (DocumentsUI)
            if self._provider() == "documentsui":
                pkg = self.driver.current_package or ""
                name_id = self._rid(pkg, self.DOCS_ITEM_TITLE_ID)
                with suppress(WebDriverException):
                    for it in self.driver.find_elements(By.ID, name_id):
                        if q.strip('"') in (it.text or ""):
                            it.click()
                            return True

            # 3) короткий скролл и повтор
            if not self._scroll_list_down():
                break

        return False

    def select_first_recent(self) -> bool:
        """Выбрать первый элемент в 'Recent'. Для системного Photo Picker кликаем кликабельного предка миниатюры."""
        pkg = self.driver.current_package or ""

        # System Photo Picker: у превью clickable=false → клик по предку
        if pkg.startswith(self.MEDIA_MODULE_PKG):
            thumbs = self.driver.find_elements(By.ID, self._rid(pkg, self.MM_THUMB_ID))
            if thumbs:
                thumb = thumbs[0]
                with suppress(NoSuchElementException, WebDriverException, StaleElementReferenceException):
                    click_target = thumb.find_element(By.XPATH, "./ancestor::*[@clickable='true'][1]")
                    click_target.click()
                    return True
                # координатный фолбэк
                with suppress(WebDriverException):
                    r = thumb.rect
                    self.driver.execute_script("mobile: clickGesture", {
                        "x": int(r["x"] + r["width"] / 2),
                        "y": int(r["y"] + r["height"] / 2)
                    })
                    return True

        # Общий путь: возьмём кликабельные элементы контейнера
        items = self._list_items(limit=6)
        if not items:
            self._scroll_list_down()
            items = self._list_items(limit=6)
        if items:
            with suppress(WebDriverException, StaleElementReferenceException):
                items[0].click()
                return True
        return False

    def confirm(self) -> None:
        """Нажать 'Готово/Выбрать', если пикер требует подтверждения (часто не требуется)."""
        pkg = self.driver.current_package or ""
        prov = self._provider()

        ids: Tuple[str, ...] = ()
        if prov == "documentsui":
            ids = tuple(self._rid(pkg, i) for i in self.DOCS_CONFIRM_IDS)
        elif prov == "photos":
            ids = tuple(self._rid(pkg, i) for i in self.PHOTOS_CONFIRM_IDS)
        elif prov == "mediamodule":
            ids = tuple(self._rid(pkg, i) for i in self.MM_CONFIRM_IDS)

        for rid in ids:
            with suppress(WebDriverException, NoSuchElementException):
                self.waits.clickable(By.ID, rid, timeout=2).click()
                return

        # текстовые кнопки
        for txt in self._OK_TEXTS:
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", f'new UiSelector().textMatches(".*{txt}.*")').click()
                return
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", f'new UiSelector().descriptionContains("{txt}")').click()
                return
        # no-op, если подтверждение не требуется

    def cancel(self) -> None:
        for txt in self._CANCEL_TEXTS:
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", f'new UiSelector().textContains("{txt}")').click()
                return
            with suppress(NoSuchElementException, WebDriverException):
                self.driver.find_element("-android uiautomator", f'new UiSelector().descriptionContains("{txt}")').click()
                return
        with suppress(WebDriverException):
            self.driver.back()

    def is_open(self) -> bool:
        return self.wait_loaded(timeout=2)

    # ======== ВНУТРЕННИЕ ПОМОЩНИКИ =========

    def _is_present(self, by, value) -> bool:
        with suppress(NoSuchElementException, WebDriverException):
            self.driver.find_element(by, value)
            return True
        return False

    def _list_container_locator(self) -> Optional[Tuple[str, str]]:
        pkg = self.driver.current_package or ""
        prov = self._provider()
        if prov == "documentsui":
            for sid in self.DOCS_LIST_IDS:
                rid = self._rid(pkg, sid)
                if self._is_present(By.ID, rid):
                    return (By.ID, rid)
        elif prov in ("photos", "mediamodule"):
            for sid in (*self.PHOTOS_GRID_IDS, *self.MM_GRID_IDS):
                rid = self._rid(pkg, sid)
                if self._is_present(By.ID, rid):
                    return (By.ID, rid)
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
        # фолбэк по всему экрану
        with suppress(WebDriverException):
            return self.driver.find_elements(By.XPATH, "//*[@clickable='true' or @focusable='true']")[:limit]
        return []

    def _scroll_list_down(self) -> bool:
        """Короткий скролл вниз в пределах контейнера."""
        loc = self._list_container_locator()
        if not loc:
            # фолбэк по экрану
            size = self.driver.get_window_size()
            x = int(size["width"] * 0.5)
            start_y = int(size["height"] * 0.75)
            end_y = int(size["height"] * 0.35)
            with suppress(WebDriverException):
                self.driver.swipe(x, start_y, x, end_y, 400)
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
                    "percent": 0.8
                },
            )
            return True
        return False
