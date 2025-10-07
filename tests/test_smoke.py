import allure

from screens.cart_screen import CartScreen
from screens.catalog_screen import CatalogScreen
from screens.main_od_screen import MainOdScreen
from components.bottom_nav import BottomNav

def test_od_enter(login, driver):
    od = MainOdScreen(driver)
    assert od.text.find_anywhere("Мои заказы", timeout=10), "Текст 'Мои заказы' не найден на экране"

def test_catalog_is_available(driver):
    nav = BottomNav(driver)
    with allure.step("Проверка каталга"):
        nav.open("Каталог")

    catalog = CatalogScreen(driver)
    # Проверяем, что открылся экран выбора поставщика
    assert catalog.catalog_screen_check(), \
        "Экран каталога не открылся - текст 'Выбирите поставщика' не найден"

    # Дополнительная проверка наличия кнопок "Создать заказ"
    buttons = catalog.text.find_all_anywhere(catalog.CREATE_ORDER_BUTTON_TEXT, timeout=10)
    assert buttons, \
        f"Кнопки '{catalog.CREATE_ORDER_BUTTON_TEXT}' не найдены в каталоге"
    assert len(buttons) > 0, \
        "В каталоге должен быть хотя бы один поставщик"


def test_cart_is_available(driver):
    nav = BottomNav(driver)
    with allure.step("Проверка корзины"):
        nav.open("Корзина")

    cart = CartScreen(driver)
    # Проверяем наличие элементов корзины
    button = cart.text.find_anywhere(cart.CREATE_ORDER_BUTTON_TEXT, timeout=10)
    currency = cart.text.find_anywhere(cart.AMOUNT_TEXT, timeout=5)

    assert button or currency, \
        "Экран корзины не открылся - ключевые элементы не найдены"


def test_more_is_available(driver):
    nav = BottomNav(driver)
    with allure.step("Проверка Еще"):
        nav.open("Еще")

def test_all_orders_check(driver):
    od = MainOdScreen(driver)
    with allure.step("Проверка Мои заказы"):
        od.all_orders_button_clik()
