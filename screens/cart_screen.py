from screens.base_screen import BaseScreen


class CartScreen(BaseScreen):
    CREATE_ORDER_BUTTON_TEXT = "Оформить"
    AMOUNT_TEXT = "₸"
    SUCCESS_TEXT = "успешно"
    BACK_BUTTON_TEXT = "Перейти"

    def create_order_button_clik(self):
        button = self.text.find_anywhere(self.CREATE_ORDER_BUTTON_TEXT, timeout=10)
        self.click_element(button)

    def verify_amount_displayed(self, amount: str = "1", timeout: int = 5) -> bool:
        amount_found = self.text.find_anywhere(amount, timeout=timeout)
        currency_found = self.text.find_anywhere(self.AMOUNT_TEXT, timeout=timeout)
        return amount_found is not None and currency_found is not None

    def success_text_check(self):
        text = self.text.find_anywhere(self.SUCCESS_TEXT, timeout=10)
        if not text:
            raise AssertionError("Текст об успешном формировании заказа не найден")

    def back_to_orders_button_clik(self):
        button = self.text.find_anywhere(self.BACK_BUTTON_TEXT, timeout=10)
        self.click_element(button)
        