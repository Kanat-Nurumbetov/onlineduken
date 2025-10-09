import pytest
import allure

from components.bottom_nav import BottomNav
from screens.payment_screen import PaymentScreen
from screens.scanner import ScannerScreen
# from screens.galery_picker import PickerScreen
from screens.galery_picker import PickerScreen
from screens.success_screen import SuccessScreen

@pytest.mark.parametrize("kind", [
    pytest.param("megapolis",  id="mega"),
    pytest.param("universal",  id="univ", marks=pytest.mark.delayed(seconds=5)),
])
def test_scan_qr_from_gallery(login, driver, clean_gallery_before_test, qr_png_on_device, kind):

    nav = BottomNav(driver)
    payments = PaymentScreen(driver)
    scanner = ScannerScreen(driver)
    picker = PickerScreen(driver)
    success_screen = SuccessScreen(driver)


    with allure.step("Открыть QR-сканер"):
        nav.find_tab_by_text("Qr")

    with allure.step("Загрузить QR из галереи"):
        scanner.tap_upload_from_gallery()
        assert picker.wait_loaded(), "Пикер не открылся"
        assert picker.select_first_recent(), "Не удалось выбрать изображение"
        picker.confirm_if_needed()


    with allure.step("Проверка заказа"):
        assert payments.verify_amount_displayed("1", timeout=5), "Сумма не отображается на экране"

    with allure.step("Нажать кнопку оплатить"):
        payments.pay_click()

    with allure.step("Ввести ОТП код для оплаты"):
        payments.confirm_payment()

    with allure.step("Ожидание обработки платежа"):
        success_screen.payment_processing_wait()

    with allure.step("Экран успеха"):
        success_screen.success_text_check()