import os
from appium.webdriver.common.appiumby import AppiumBy as By
from screens.base_screen import BaseScreen
from screens.login_screen import LoginScreen

class PaymentScreen(BaseScreen):
    PAY_BUTTON_TEXT = "Оплатить"
    BANK_ACCOUNT_TEXT = "account-tenge"
    AMOUNT_TEXT = "₸"
    CONTRACT_ID_TEXT = ""
    DISTRIBUTOR_TEXT = ""
    CLIENT_IIN_TEXT = ""
    ORDER_DATE_TEXT = ""
    MANAGER_TEXT = "менеджер"

    def pay_click(self):
        element = self.text.find_anywhere(self.PAY_BUTTON_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise Exception(f"Элемент '{self.PAY_BUTTON_TEXT}' не найден на экране")

    def select_bank_account(self):
        element = self.text.find_anywhere(self.BANK_ACCOUNT_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise Exception(f"Элемент '{self.BANK_ACCOUNT_TEXT}' не найден на экране")
        # Добавить проверку вплывающего модального окна и выбор счета

    def order_information_check(self):
        contract = self.text.find_anywhere(self.AMOUNT_TEXT, timeout=10)
        assert contract is not None
        distributor = self.text.find_anywhere(self.DISTRIBUTOR_TEXT, timeout=10)
        assert distributor is not None
        client_iin = self.text.find_anywhere(self.CLIENT_IIN_TEXT, timeout=10)
        def_iin = os.getenv("QR_DEFAULT_IIN", "")
        assert client_iin == def_iin
        order_date = self.text.find_anywhere(self.ORDER_DATE_TEXT, timeout=10)
        assert order_date is not None

    def confirm_payment(self):
        login = LoginScreen(self.driver)
        login.confirmation_code_enter("123456")