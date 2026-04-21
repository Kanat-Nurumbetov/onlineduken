from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from mobile_automation.config import Settings

try:
    import allure
    from allure_commons.types import AttachmentType
except Exception:  # pragma: no cover
    allure = None
    AttachmentType = None


def allure_enabled() -> bool:
    return allure is not None and AttachmentType is not None


def write_allure_environment(results_dir: str | Path, settings: Settings) -> None:
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    values = {
        "TARGET": settings.target,
        "PLATFORM": settings.platform,
        "ONLINEDUKEN_ENTRY_MODE": settings.onlineduken_entry_mode,
        "IS_BROWSERSTACK": str(settings.is_browserstack).lower(),
        "ANDROID_DEVICE_NAME": settings.android_device_name,
        "ANDROID_UDID": settings.android_udid,
        "BROWSERSTACK_PROJECT_NAME": settings.browserstack_project_name,
        "BROWSERSTACK_BUILD_NAME": settings.browserstack_build_name,
        "CLIENT_BIN_CONFIGURED": str(bool(settings.client_bin)).lower(),
        "INVOICE_REFERENCE_CONFIGURED": str(bool(settings.invoice_reference)).lower(),
    }
    body = "\n".join(f"{key}={value}" for key, value in values.items())
    (results_path / "environment.properties").write_text(body + "\n", encoding="utf-8")


def attach_text(name: str, text: str) -> None:
    if not allure_enabled() or not text:
        return
    allure.attach(text, name=name, attachment_type=AttachmentType.TEXT)


def attach_json(name: str, payload: dict[str, Any]) -> None:
    if not allure_enabled():
        return
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name=name,
        attachment_type=AttachmentType.JSON,
    )


def attach_driver_state(driver, label_prefix: str = "driver") -> None:
    if not allure_enabled() or driver is None:
        return

    metadata: dict[str, Any] = {
        "session_id": getattr(driver, "session_id", ""),
    }

    for field_name in ("current_context", "current_package", "current_activity"):
        with suppress(Exception):
            metadata[field_name] = getattr(driver, field_name)

    with suppress(Exception):
        metadata["contexts"] = list(driver.contexts)

    with suppress(Exception):
        metadata["current_url"] = driver.current_url

    with suppress(Exception):
        screenshot = driver.get_screenshot_as_png()
        if screenshot:
            allure.attach(
                screenshot,
                name=f"{label_prefix}_screenshot",
                attachment_type=AttachmentType.PNG,
            )

    with suppress(Exception):
        page_source = driver.page_source
        if page_source:
            attach_text(f"{label_prefix}_page_source", page_source)

    attach_json(f"{label_prefix}_metadata", metadata)
