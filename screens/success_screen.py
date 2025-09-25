from selenium.webdriver.common.by import By
from screens.base_screen import BaseScreen
import time

class SuccessScreen(BaseScreen):
    SUCCESS_TEXT = "Оплата прошла успешно"
    INVOISE_TEXT = "Платежное поручение"
    BONUS_BOCK_TEXT = "Вы получили"
    FEEDBACK_TEXT = "Поставьте оценку заказу"
    BACK_TO_ORDERS_BUTTON_TEXT = "Перейти к Заказам"
    PAYMENT_PROCESSING_TEXT = "Платеж в обработке"

    def payment_processing_wait(self, timeout: int = 15) -> None:
        end = time.monotonic() + timeout
        # Опционально: подождать, чтобы спиннер успел появиться
        self.text.present_anywhere(self.PAYMENT_PROCESSING_TEXT, timeout=1)

        while time.monotonic() < end:
            if not self.text.present_anywhere(self.PAYMENT_PROCESSING_TEXT, timeout=1):
                return
            time.sleep(0.3)

        raise AssertionError(f"«{self.PAYMENT_PROCESSING_TEXT}» не исчез за {timeout} c")

    def back_to_orders_button_clik(self):
        button = self.text.find_anywhere(self.BACK_TO_ORDERS_BUTTON_TEXT, timeout=10)
        self.click_element(button)

    def success_text_check(self):
        assert self.text.find_anywhere(self.SUCCESS_TEXT, timeout=60)

    def invoise_text_check(self):
        assert self.text.find_anywhere(self.INVOISE_TEXT, timeout=10)

    def bonus_block_text_check(self):
        assert self.text.find_anywhere(self.BONUS_BOCK_TEXT, timeout=10)

    def feedback_text_check(self):
        assert self.text.find_anywhere(self.FEEDBACK_TEXT, timeout=10)
