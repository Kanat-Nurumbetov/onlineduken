from screens.base_screen import BaseScreen

class MainOdScreen(BaseScreen):
    BONUS_BUTTON_TEXT = "bonus"
    ALL_ORDERS_BUTTON_TEXT = "Мои заказы"
    CREATE_ORDER_BUTTON_TEXT = "Создать заказ"
    ALL_DISTRIBUTORS_TEXT = "Всеgreen-arrow"
    ALL_GOODS_TEXT = "Все товары"

    def create_order_button_clik(self):
        button = self.text.find_anywhere(self.CREATE_ORDER_BUTTON_TEXT, timeout=10)
        self.click_element(button)

    def bonus_button_clik(self):
        bonus_button = self.text.find_anywhere(self.BONUS_BUTTON_TEXT, timeout=10)
        self.click_element(bonus_button)

    def all_orders_button_clik(self):
        all_orders_button = self.text.find_anywhere(self.ALL_ORDERS_BUTTON_TEXT, timeout=10)
        self.click_element(all_orders_button)

    def all_distributors_button_clik(self):
        all_distributors_button = self.text.find_anywhere(self.ALL_DISTRIBUTORS_TEXT, timeout=10)
        self.click_element(all_distributors_button)

    def all_goods_button_clik(self):
        all_goods_button = self.text.find_anywhere(self.ALL_GOODS_TEXT, timeout=10)
        self.click_element(all_goods_button)




