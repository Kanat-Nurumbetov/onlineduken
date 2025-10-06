from screens.base_screen import BaseScreen

class CatalogScreen(BaseScreen):
    DISTR_CHOISE_TEXT = "Выбирите поставщика"
    CREATE_ORDER_BUTTON_TEXT = "Создать заказ"
    ADD_TO_CART_BUTTON_TEXT = "корзину"

    def catalog_screen_check(self):
        text_found = self.text.find_anywhere(self.DISTR_CHOISE_TEXT, timeout=10)
        return text_found is not None

    def enter_to_distr_catalog(self):
        buttons = self.text.find_all_anywhere(self.CREATE_ORDER_BUTTON_TEXT, timeout=10)

        if not buttons:
            raise AssertionError(f"Ни одной кнопки '{self.CREATE_ORDER_BUTTON_TEXT}' не найдено")

        self.click_element(buttons[0])

    def enter_to_product_card(self):
        buttons = self.text.find_all_anywhere(self.ADD_TO_CART_BUTTON_TEXT, timeout=10)

        if not buttons:
            raise AssertionError(f"Ни одной кнопки '{self.ADD_TO_CART_BUTTON_TEXT}' не найдено")

        self.click_element(buttons[0])

    def add_to_cart_button_clik(self):
        button = self.text.find_anywhere(self.ADD_TO_CART_BUTTON_TEXT, timeout=10)

        if not button:
            raise AssertionError(f"Ни одной кнопки '{self.ADD_TO_CART_BUTTON_TEXT}' не найдено")

        self.click_element(button)