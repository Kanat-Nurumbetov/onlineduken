import pytest
import allure

from components.bottom_nav import BottomNav
from screens.payment_screen import PaymentScreen
from screens.scanner import ScannerScreen
# from screens.galery_picker import PickerScreen
from screens.galery_picker import PickerScreen
from screens.success_screen import SuccessScreen

@pytest.mark.parametrize("kind", ["megapolis", "universal"])
def test_scan_qr_from_gallery(login, driver, clean_gallery_before_test, qr_png_on_device, kind):

    nav = BottomNav(driver)
    payments = PaymentScreen(driver)
    scanner = ScannerScreen(driver)
    picker = PickerScreen(driver)
    success_screen = SuccessScreen(driver)


    with allure.step("Открыть QR-сканер"):
        nav.open("QR")

    with allure.step("Загрузить QR из галереи"):
        scanner.tap_upload_from_gallery()
        assert picker.wait_loaded(), "Пикер не открылся"
        assert picker.select_first_recent(), "Не удалось выбрать изображение"
        picker.confirm_if_needed()



    with allure.step("Проверка заказа"):
        payments.order_information_check()

    with allure.step("Нажать кнопку оплатить"):
        payments.confirm_payment()

    with allure.step("Ввести ОТП код для оплаты"):
        payments.confirm_payment()

    with allure.step("Экран успеха"):
        success_screen.success_text_check()