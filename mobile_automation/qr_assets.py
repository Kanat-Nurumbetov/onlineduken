from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import qrcode

from mobile_automation.config import GeneratedQrCase, Settings


def ensure_qr_image(settings: Settings) -> str:
    if settings.qr_image_path:
        return settings.qr_image_path

    qr_content = settings.qr_source_url or settings.qr_source_payload
    if not qr_content:
        return ""

    target_path = Path(settings.qr_generated_image_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(target_path)
    return str(target_path)


def _build_qr_png(payload: str, target_path: Path) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(target_path)
    return str(target_path)


def _build_unique_numeric_value(base_value: str, unique_seed: str, min_prefix: str = "1") -> str:
    numeric_base = "".join(character for character in base_value if character.isdigit()) or min_prefix
    return f"{numeric_base}{unique_seed}"[-18:]


def _build_unique_seed() -> str:
    return datetime.now(UTC).strftime("%y%m%d%H%M%S%f")[-12:]


def build_generated_qr_cases(settings: Settings) -> list[GeneratedQrCase]:
    cases: list[GeneratedQrCase] = []
    base_path = Path(settings.qr_generated_image_path)

    if not settings.client_bin:
        return cases

    unique_seed = _build_unique_seed()
    unique_invoice_id = _build_unique_numeric_value(settings.qr_invoice_id, unique_seed)
    unique_invoice_title = _build_unique_numeric_value(settings.qr_invoice_title, unique_seed)
    unique_contract = _build_unique_numeric_value(settings.qr_megapolis_contract, unique_seed)

    template_values = {
        "client_bin": quote(settings.client_bin, safe=""),
        "invoice_id": quote(unique_invoice_id, safe=""),
        "amount": quote(settings.qr_amount, safe=""),
        "invoice_title": quote(unique_invoice_title, safe=""),
        "contract": quote(unique_contract, safe=""),
    }

    if settings.qr_common_enabled and settings.qr_common_template:
        payload = settings.qr_common_template.format(**template_values)
        image_path = _build_qr_png(payload, base_path.with_name(f"generated_qr_common_{unique_seed}.png"))
        cases.append(GeneratedQrCase(name="common", image_path=image_path, payload=payload))

    if settings.qr_megapolis_enabled and settings.qr_megapolis_template:
        payload = settings.qr_megapolis_template.format(**template_values)
        image_path = _build_qr_png(payload, base_path.with_name(f"generated_qr_megapolis_{unique_seed}.png"))
        cases.append(GeneratedQrCase(name="megapolis", image_path=image_path, payload=payload))

    return cases
