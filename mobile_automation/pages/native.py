from __future__ import annotations

from selenium.webdriver.common.by import By

from mobile_automation.android_ids import app_id

# Note on the mojibake-looking strings (e.g. "РћРїР»Р°С‚"):
# these are intentional fallbacks for environments where the Halyk stage build
# renders Cyrillic UI text that has been double-encoded as CP1251 → UTF-8.
# They match the same words ("Оплат", "Подпис", "Подтверж") in the corrupted
# byte form so XPath locators stay green regardless of which encoding the
# emulator surfaces. Don't remove them without verifying both local and
# BrowserStack builds render Cyrillic correctly.


class LoginPage:
    PHONE_INPUT = (By.ID, app_id("phone_input"))
    LOGIN_BUTTON = (By.ID, app_id("login_button"))
    LANGUAGE = (By.ID, app_id("lang_text_view"))
    BECOME_CUSTOMER = (By.ID, app_id("become_client_button"))


class SmsCodePage:
    SUBTITLE = (By.ID, app_id("sms_subtitle"))
    TIMER = (By.ID, app_id("sms_remaining"))
    CODE_INPUT = (By.ID, app_id("et"))


class PasscodePage:
    INPUT = (By.ID, app_id("pinEditText"))
    FORGOT = (By.ID, app_id("text_forgot_pin"))


class MainHomePage:
    CONTRACT_SELECTOR = (By.ID, app_id("select_contract_container"))
    CONTRACT_NAME = (By.ID, app_id("contract_name_text_view"))
    CONTRACT_LIST = (By.ID, app_id("rv_contracts"))
    ONLINE_DUKEN_SHORTCUT = (
        By.XPATH,
        f"//androidx.recyclerview.widget.RecyclerView[@resource-id='{app_id('shortcut_rv')}']"
        f"//android.view.ViewGroup[@resource-id='{app_id('container')}']"
        f"[.//android.widget.TextView[@resource-id='{app_id('title')}' and contains(@text, 'Online')]]",
    )
    ONLINE_DUKEN_SECTION = (
        By.XPATH,
        f"//android.widget.TextView[@resource-id='{app_id('tv_header')}' and contains(@text, 'Online')]"
        "/following-sibling::android.widget.FrameLayout"
        f"//android.view.ViewGroup[@resource-id='{app_id('products_container')}']",
    )


class B2BWebViewPage:
    WEBVIEW = (By.ID, app_id("webview"))


class MainPromptPage:
    NEXT_BUTTON = (By.ID, app_id("successButtonNext"))


class OnlineDukenNativeHomePage:
    QR_TAB = (By.XPATH, "//*[@content-desc='QR']")


class QrScannerPage:
    TITLE = (By.XPATH, "//*[contains(@text, 'QR') or contains(@text, 'Р QR')]")
    GALLERY_BUTTON = (By.ID, app_id("gallery"))
    FLASHLIGHT_BUTTON = (By.ID, app_id("light"))
    INSTRUCTION_TEXT = (By.ID, app_id("text_view"))


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
    CODE_INPUT = (By.ID, app_id("et"))
