import os
import re
from screens.base_screen import BaseScreen
from screens.login_screen import LoginScreen
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


class PaymentScreen(BaseScreen):
    PAY_BUTTON_TEXT = "Оплатить"
    BANK_ACCOUNT_TEXT = "account-tenge"
    AMOUNT_TEXT = "₸"
    MANAGER_TEXT = "менеджер"

    def pay_click(self):
        element = self.text.find_anywhere(self.PAY_BUTTON_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise AssertionError(f"Элемент '{self.PAY_BUTTON_TEXT}' не найден на экране")

    def select_bank_account(self):
        element = self.text.find_anywhere(self.BANK_ACCOUNT_TEXT, timeout=10)
        if element:
            element.click()
        else:
            raise AssertionError(f"Элемент '{self.BANK_ACCOUNT_TEXT}' не найден на экране")

    def _extract_text(self, found) -> str:
        """Безопасно получить текст: учитывает контекст, stale и даёт фолбэк."""
        orig = getattr(self.driver, "current_context", "NATIVE_APP")
        try:
            # 1) перейти в контекст, где найден элемент
            if orig != found.context:
                self.driver.switch_to.context(found.context)

            # 2) попробовать обычные атрибуты
            try:
                txt = (found.element.text or "").strip()
                if not txt:
                    txt = (found.element.get_attribute("content-desc") or "").strip()
                if txt:
                    return txt
            except (NoSuchElementException, StaleElementReferenceException):
                pass  # упал — попробуем фолбэки ниже

            # 3) фолбэк: целиком текст экрана текущего контекста
            if str(found.context).startswith("WEBVIEW"):
                try:
                    inner = self.driver.execute_script(
                        "return (document.body && (document.body.innerText || document.body.textContent)) || '';"
                    )
                    return inner or ""
                except Exception:
                    return ""
            else:
                return self.driver.page_source or ""

        finally:
            # вернуть исходный контекст
            if getattr(self.driver, "current_context", None) != orig:
                self.driver.switch_to.context(orig)

    @staticmethod
    def _parse_multi(value: str) -> list[str]:
        """Парсит строку вида 'a,b c;d' в список ['a','b','c','d'] без пустых."""
        if not value:
            return []
        parts = re.split(r'[,\s;]+', value.strip())
        return [p for p in parts if p]

    def order_information_check(self):
        """Проверка ключевых реквизитов заказа по значениям из окружения."""
        distributors = self._parse_multi(value=os.getenv("QR_DISTRIBUTOR_LIST", ""))
        if not distributors:
            single = os.getenv("QR_DEFAULT_DISTRIBUTOR", "")
            distributors = [single] if single else []

        expected_map = {
            "iin": os.getenv("QR_DEFAULT_IIN", ""),
            "client": os.getenv("QR_DEFAULT_CLIENT", ""),
            "distributor": distributors,
            "amount": os.getenv("QR_DEFAULT_AMOUNT", ""),
        }

        for field, values in expected_map.items():
            expected_values = [str(v) for v in values if str(v)]
            if not expected_values:
                continue

            matched_value = None
            matched_text = "None"

            for val in expected_values:
                found = self.text.find_anywhere(val, timeout=5)
                if not found:
                    continue
                actual_text = self._extract_text(found)
                if val in actual_text:
                    matched_value = val
                    matched_text = actual_text
                    break

            # если ничего не нашли — падаем с понятным сообщением
            assert matched_value is not None, (
                f"Поле '{field}' не найдено. "
                f"Ожидалось одно из: {', '.join(expected_values)}"
            )

            # дополнительная защита (обычно уже true)
            assert matched_value in matched_text, (
                f"Поле '{field}' содержит '{matched_text}', ожидалось '{matched_value}'"
            )

    def confirm_payment(self):
        login = LoginScreen(self.driver)
        login.confirmation_code_enter("123456")
