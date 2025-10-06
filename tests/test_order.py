import allure

from components.bottom_nav import BottomNav
from screens.catalog_screen import CatalogScreen
from screens.cart_screen import CartScreen


def test_add_to_cart(login, driver):
    catalog = CatalogScreen(driver)
    cart = CartScreen(driver)
    nav = BottomNav(driver)

    with allure.step("Переход в каталог"):
        nav.open("Каталог")

    with allure.step("Переход в католог дистра"):
        catalog.enter_to_distr_catalog()

    with allure.step("Переход в карточку товара"):
        catalog.enter_to_product_card()

    with allure.step("Добавление товара в корзину"):
        catalog.add_to_cart_button_clik()
        catalog.add_to_cart_button_clik()

    with allure.step("Переход в Корзину"):
        nav.open("Корзина")

    with allure.step("Проверка корзины"):
        cart.verify_amount_displayed()

    with allure.step("Формирование заказа"):
        cart.create_order_button_clik()

    with allure.step("Проверка успешного созания"):
        cart.success_text_check()


