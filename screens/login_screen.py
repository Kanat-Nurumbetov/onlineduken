from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from screens.base_screen import BaseScreen

class LoginScreen(BaseScreen):
    PHONE_INPUT_ID = "kz.halyk.onlinebank.stage:id/phone_input"
    LOGIN_BUTTON_ID = "kz.halyk.onlinebank.stage:id/login_button"
    CONFIRMATION_CODE_INPUT_ID = "kz.halyk.onlinebank.stage:id/et"
    ZERO_INT_XPATH = '//android.view.ViewGroup[@resource-id="kz.halyk.onlinebank.stage:id/passcode_fragment_keyboard"]/android.widget.FrameLayout[10]/android.widget.FrameLayout/android.widget.LinearLayout'
    GEO_PERMISSION_ID = "kz.halyk.onlinebank.stage:id/successButtonNext"
    MORE_MENU_ID = "kz.halyk.onlinebank.stage:id/navigation_more"
    ONLINE_DUKEN_TEXT = "Duken"

    def phone_enter(self, phone):
        field = self.waits.el_clickable(By.ID, self.PHONE_INPUT_ID)
        if not field:
            raise TimeoutException("Поле ввода телефона недоступно")
        field.send_keys(phone)

    def login_click(self):
        login = self.waits.el_clickable(By.ID, self.LOGIN_BUTTON_ID)
        if not login:
            raise TimeoutException("Кнопка входа недоступна")
        self.click_element(login)

    def confirmation_code_enter(self, code):
        code_field = self.waits.el_clickable(By.ID, self.CONFIRMATION_CODE_INPUT_ID)
        if not code_field:
            raise TimeoutException("Поле ввода проверочного кода недоступно")
        code_field.send_keys(code)

    def quik_pin_setup(self):
        for _ in range(4):
            el = self.waits.el_clickable(By.XPATH, self.ZERO_INT_XPATH)
            if not el:
                raise TimeoutException("Кнопка '0' для ввода PIN недоступна")
            el.click()

    def geo_permission(self):
        button = self.waits.el_clickable(By.ID, self.GEO_PERMISSION_ID)
        if not button:
            raise TimeoutException("Кнопка разрешения геолокации недоступна")
        button.click()

    def online_duken(self):
        element = self.text.find_anywhere(self.ONLINE_DUKEN_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise Exception(f"Элемент '{self.ONLINE_DUKEN_TEXT}' не найден на экране")
