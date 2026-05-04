from __future__ import annotations

from selenium.webdriver.common.by import By


class LoginPage:
    PHONE_INPUT = (By.ID, "kz.halyk.onlinebank.stage:id/phone_input")
    LOGIN_BUTTON = (By.ID, "kz.halyk.onlinebank.stage:id/login_button")
    LANGUAGE = (By.ID, "kz.halyk.onlinebank.stage:id/lang_text_view")
    BECOME_CUSTOMER = (By.ID, "kz.halyk.onlinebank.stage:id/become_client_button")


class SmsCodePage:
    SUBTITLE = (By.ID, "kz.halyk.onlinebank.stage:id/sms_subtitle")
    TIMER = (By.ID, "kz.halyk.onlinebank.stage:id/sms_remaining")
    CODE_INPUT = (By.ID, "kz.halyk.onlinebank.stage:id/et")


class PasscodePage:
    INPUT = (By.ID, "kz.halyk.onlinebank.stage:id/pinEditText")
    FORGOT = (By.ID, "kz.halyk.onlinebank.stage:id/text_forgot_pin")


class MainHomePage:
    CONTRACT_SELECTOR = (By.ID, "kz.halyk.onlinebank.stage:id/select_contract_container")
    CONTRACT_NAME = (By.ID, "kz.halyk.onlinebank.stage:id/contract_name_text_view")
    CONTRACT_LIST = (By.ID, "kz.halyk.onlinebank.stage:id/rv_contracts")
    ONLINE_DUKEN_SHORTCUT = (
        By.XPATH,
        "//androidx.recyclerview.widget.RecyclerView[@resource-id='kz.halyk.onlinebank.stage:id/shortcut_rv']"
        "//android.view.ViewGroup[@resource-id='kz.halyk.onlinebank.stage:id/container']"
        "[.//android.widget.TextView[@resource-id='kz.halyk.onlinebank.stage:id/title' and contains(@text, 'Online')]]",
    )
    ONLINE_DUKEN_SECTION = (
        By.XPATH,
        "//android.widget.TextView[@resource-id='kz.halyk.onlinebank.stage:id/tv_header' and contains(@text, 'Online')]"
        "/following-sibling::android.widget.FrameLayout"
        "//android.view.ViewGroup[@resource-id='kz.halyk.onlinebank.stage:id/products_container']",
    )


class B2BWebViewPage:
    WEBVIEW = (By.ID, "kz.halyk.onlinebank.stage:id/webview")


class MainPromptPage:
    NEXT_BUTTON = (By.ID, "kz.halyk.onlinebank.stage:id/successButtonNext")


class OnlineDukenNativeHomePage:
    QR_TAB = (By.XPATH, "//*[@content-desc='QR']")


class QrScannerPage:
    TITLE = (By.XPATH, "//*[contains(@text, 'QR') or contains(@text, 'Р QR')]")
    GALLERY_BUTTON = (By.ID, "kz.halyk.onlinebank.stage:id/gallery")
    FLASHLIGHT_BUTTON = (By.ID, "kz.halyk.onlinebank.stage:id/light")
    INSTRUCTION_TEXT = (By.ID, "kz.halyk.onlinebank.stage:id/text_view")


class PhotoPickerPage:
    ROOT = (
        By.XPATH,
        "//*[contains(@package, 'photopicker') or contains(@package, 'picker') "
        "or contains(@package, 'providers.media.module') "
        "or @resource-id='com.google.android.providers.media.module:id/picker_tab_recyclerview']",
    )
    DISMISS_BUTTON = (By.XPATH, "//*[contains(@text, 'Dismiss')]")
    FIRST_PHOTO = (
        By.XPATH,
        "(//*[contains(@content-desc, 'Photo taken') and @clickable='true'])[1]",
    )
    FIRST_GRID_ITEM = (By.XPATH, "(//*[@clickable='true' and @long-clickable='true'])[1]")


class NativePaymentPage:
    TITLE = (
        By.XPATH,
        "//*[contains(@text, 'Оплат') or contains(@text, 'Подпис') or contains(@text, 'РћРїР»Р°С‚') or contains(@text, 'РџРѕРґРїРёСЃ')]",
    )
    PAY_BUTTON = (
        By.XPATH,
        "//android.widget.Button[@text='Оплатить' or @text='Подписать' or @text='РћРїР»Р°С‚РёС‚СЊ' or @text='РџРѕРґРїРёСЃР°С‚СЊ']",
    )
    TOAST_CONTAINER = (By.XPATH, "//*[@resource-id='toast-container']")


class PaymentConfirmationPage:
    TITLE = (By.XPATH, "//*[contains(@text, 'Подтверж') or contains(@text, 'РџРѕРґС‚РІРµСЂР¶')]")
    CODE_INPUT = (By.ID, "kz.halyk.onlinebank.stage:id/et")
