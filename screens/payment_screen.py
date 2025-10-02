
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

    def verify_amount_displayed(self, amount: str = "1", timeout: int = 5) -> bool:
        """Проверяет, что сумма и символ валюты отображаются на экране"""
        amount_found = self.text.find_anywhere(amount, timeout=timeout)
        currency_found = self.text.find_anywhere(self.AMOUNT_TEXT, timeout=timeout)
        return amount_found is not None and currency_found is not None

    def select_bank_account(self):
        element = self.text.find_anywhere(self.BANK_ACCOUNT_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise AssertionError(f"Элемент '{self.BANK_ACCOUNT_TEXT}' не найден на экране")

    def confirm_payment(self):
        login = LoginScreen(self.driver)
        login.confirmation_code_enter("123456")
