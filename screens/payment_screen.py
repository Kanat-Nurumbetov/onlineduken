import os

from screens.base_screen import BaseScreen
from screens.login_screen import LoginScreen


class PaymentScreen(BaseScreen):
    PAY_BUTTON_TEXT = "Оплатить"
    BANK_ACCOUNT_TEXT = "account-tenge"
    AMOUNT_TEXT = "₸"
    MANAGER_TEXT = "менеджер"

    def pay_click(self):
        element = self.text.find_anywhere(self.PAY_BUTTON_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise AssertionError(f"Элемент '{self.PAY_BUTTON_TEXT}' не найден на экране")

    def select_bank_account(self):
        element = self.text.find_anywhere(self.BANK_ACCOUNT_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise AssertionError(f"Элемент '{self.BANK_ACCOUNT_TEXT}' не найден на экране")

    def _extract_text(self, found) -> str:
        """Извлекает текст из элемента с учетом разных атрибутов."""

        text = (getattr(found.element, "text", None) or "").strip()
        if not text:
            text = (found.element.get_attribute("value") or "").strip()
        if not text:
            text = (found.element.get_attribute("label") or "").strip()
        return text

    def order_information_check(self):
        """Проверка ключевых реквизитов заказа по значениям из окружения."""

        expected_map = {
            "iin": os.getenv("QR_DEFAULT_IIN", ""),
            "client": os.getenv("QR_DEFAULT_CLIENT", ""),
            "distributor": os.getenv("QR_DEFAULT_DISTRIBUTOR", ""),
            "amount": os.getenv("QR_DEFAULT_AMOUNT", ""),
        }

        for field, expected in expected_map.items():
            if not expected:
                continue

            found = self.text.find_anywhere(str(expected), timeout=10)
            assert found is not None, f"Поле '{field}' со значением '{expected}' не найдено на экране"

            actual_text = self._extract_text(found)
            assert str(expected) in actual_text, (
                f"Поле '{field}' содержит '{actual_text}', ожидалось значение '{expected}'"
            )

    def confirm_payment(self):
        login = LoginScreen(self.driver)
        login.confirmation_code_enter("123456")
