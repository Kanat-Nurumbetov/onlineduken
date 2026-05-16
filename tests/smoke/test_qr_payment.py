from __future__ import annotations

import allure
import pytest

from mobile_automation.qr_flow import run_qr_gallery_payment_flow
from tests.smoke._smoke_helpers import get_qr_case


@allure.epic("OnlineDuken")
@allure.feature("Smoke")
@allure.feature("Payments")
@allure.story("QR Payment")
@allure.title("Complete QR payment flow via gallery: {qr_case_name}")
@pytest.mark.smoke
@pytest.mark.payments
@pytest.mark.native
@pytest.mark.browserstack_safe
@pytest.mark.parametrize("qr_case_name", ["common", "megapolis"], ids=["qr-common", "qr-megapolis"])
def test_smoke_qr_payment_flow(payments_smoke_driver, settings, generated_qr_cases, qr_case_name):
    qr_case = get_qr_case(generated_qr_cases, qr_case_name)
    if not qr_case:
        pytest.skip(
            f"QR case '{qr_case_name}' is not configured yet. "
            "Set CLIENT_BIN and QR template/env values for the requested QR type."
        )
    with allure.step(f"Run QR gallery payment flow for case '{qr_case_name}'"):
        result = run_qr_gallery_payment_flow(payments_smoke_driver, settings, qr_case)
        assert result
