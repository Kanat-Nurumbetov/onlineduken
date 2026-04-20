from __future__ import annotations

from selenium.webdriver.common.by import By


class OnlineDukenHomePage:
    ORDERS_LINK = (By.CSS_SELECTOR, 'a[href="/web/customer-frontend/orders"]')
    BONUSES_LINK = (By.CSS_SELECTOR, 'a[href="/web/customer-frontend/bonuses"]')
    PAYMENT_LINK = (
        By.CSS_SELECTOR,
        'a[href="/web/customer-frontend/distributor/qr-distributor"], '
        'a[href="/web/customer-frontend/distributors/qr-distributor"], '
        'a[href="/web/customer-frontend/distributors/qr-distributors"]',
    )
    HOME_TAB = (By.CSS_SELECTOR, 'a[href="/web/customer-frontend/"]')
    CATALOG_TAB = (
        By.CSS_SELECTOR,
        'a[href="/web/customer-frontend/distributor"], a[href="/web/customer-frontend/distributors"]',
    )
    CART_TAB = (By.CSS_SELECTOR, 'a[href="/web/customer-frontend/cart"]')
    MORE_TAB = (By.CSS_SELECTOR, 'a[href="/web/customer-frontend/more"]')
    BANNER_BUTTON = (By.CSS_SELECTOR, "button.banner-btn")
    ADD_TO_CART_BUTTON = (By.XPATH, "//button[normalize-space()='\u0412 \u043a\u043e\u0440\u0437\u0438\u043d\u0443']")
    CREATE_ORDER_BUTTON = (By.XPATH, "//button[normalize-space()='\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u043a\u0430\u0437']")


class CatalogPage:
    ROOT = (By.CSS_SELECTOR, "hb2b-distributor")
    TITLE = (By.CSS_SELECTOR, 'input[placeholder="\u041d\u0430\u0439\u0442\u0438 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430"]')
    SUPPLIER_CARDS = (By.CSS_SELECTOR, "div.distributor-card, [class*='distributor-card']")
    EMPTY_STATE = (By.CSS_SELECTOR, "div.search-centered")
    CREATE_ORDER_BUTTONS = (By.XPATH, "//button[normalize-space()='\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u043a\u0430\u0437']")
    ADD_TO_CART_BUTTONS = (By.XPATH, "//button[normalize-space()='\u0412 \u043a\u043e\u0440\u0437\u0438\u043d\u0443']")


class OrdersPage:
    TITLE = (By.CSS_SELECTOR, "h1.mobile-page-header__title")


class BonusesPage:
    TITLE = (By.CSS_SELECTOR, "h1.mobile-page-header__title")
    HISTORY_LINK = (By.CSS_SELECTOR, 'div.card.card-item[routerlink="./history"]')


class PaymentPage:
    TITLE = (By.CSS_SELECTOR, "h1.mobile-page-header__title")
    ALL_TAB = (By.XPATH, "//button[normalize-space()='\u0412\u0441\u0435']")
    MANUAL_PAYMENT_TAB = (By.XPATH, "//button[normalize-space()='\u0420\u0443\u0447\u043d\u0430\u044f \u043e\u043f\u043b\u0430\u0442\u0430']")
    QR_PAYMENT_TAB = (By.XPATH, "//button[normalize-space()='QR \u043e\u043f\u043b\u0430\u0442\u0430']")


class CartPage:
    TITLE = (By.CSS_SELECTOR, "h1.mobile-page-header__title")
    CREATE_ORDER_BUTTON = (By.XPATH, "//button[normalize-space()='\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u043a\u0430\u0437']")
    EMPTY_STATE = (By.XPATH, "//*[contains(normalize-space(), '\u043a\u043e\u0440\u0437\u0438\u043d') and contains(normalize-space(), '\u043f\u0443\u0441\u0442')]")


class OrderResultPage:
    RETURN_TO_ORDERS_BUTTON = (
        By.XPATH,
        "//*[self::button or self::a][contains(normalize-space(), '\u0412\u0435\u0440\u043d\u0443\u0442\u044c') and contains(normalize-space(), '\u0437\u0430\u043a\u0430\u0437')]",
    )


class MorePage:
    TITLE = (By.CSS_SELECTOR, "h1.mobile-page-header__title")
    CASHIERS_ITEM = (By.XPATH, "//*[normalize-space()='\u041a\u0430\u0441\u0441\u0438\u0440\u044b Online Duken']")
    EXIT_ITEM = (By.XPATH, "//*[contains(normalize-space(),'\u0412\u044b\u0439\u0442\u0438 \u0438\u0437 OnlineDuken')]")
