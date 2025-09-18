import pytest
import allure

from components.bottom_nav import BottomNav
# from screens.payments import PaymentsScreen
from screens.scanner import ScannerScreen
from screens.galery_picker import PickerScreen  # экран системного/встроенного пикера

@pytest.mark.parametrize("kind", ["megapolis", "universal"])
def test_scan_qr_from_gallery(login, driver, clean_gallery_before_test, qr_png_on_device, kind):
    # qr_png_on_device → твоя фикстура, которая:
    # 1) генерит PNG через QrGenerator().png(kind)
    # 2) кладёт его в /sdcard/Pictures/... и триггерит медиасканер
    # 3) возвращает dict с полями: name, local, device

    nav = BottomNav(driver)
    # payments = PaymentsScreen(driver)
    scanner = ScannerScreen(driver)
    picker = PickerScreen(driver)

    with allure.step("Открыть QR-сканер"):
        nav.open("QR")

    with allure.step("Загрузить QR из галереи"):
        scanner.tap_upload_from_gallery()           # кнопка "Загрузить с галереи"
        # В некоторых пикерах имя файла видно сразу; если нет — выбери первый в 'Недавние'
        selected = picker.select_file_by_name(qr_png_on_device["local"].name)
        if not selected:
            selected = picker.select_first_recent()

        assert selected, "Не удалось выбрать тестовый QR-файл ни по имени, ни через 'Недавние'"

        picker.confirm()

