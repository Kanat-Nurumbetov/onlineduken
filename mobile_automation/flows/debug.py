"""Debug-artifact helpers.

Each `capture_*_debug_state` writes a triple (`<prefix>.txt`, `<prefix>.xml|.html`,
`<prefix>.png`) under `artifacts/` so that a failed run can be triaged without
needing to reproduce it. The Allure `attach_driver_state` hook in
`tests/conftest.py` does the same thing at the pytest level.
"""

from __future__ import annotations

from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"


def capture_native_debug_state(driver, prefix: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = ARTIFACTS_DIR / f"{prefix}.png"
    source_path = ARTIFACTS_DIR / f"{prefix}.xml"
    meta_path = ARTIFACTS_DIR / f"{prefix}.txt"

    screenshot_saved = False
    with meta_path.open("w", encoding="utf-8") as meta_file:
        for label, getter in (
            ("current_activity", lambda: getattr(driver, "current_activity", "")),
            ("current_package", lambda: getattr(driver, "current_package", "")),
            ("contexts", lambda: ",".join(driver.contexts)),
        ):
            try:
                meta_file.write(f"{label}={getter()}\n")
            except Exception as exc:  # pragma: no cover - debug helper only
                meta_file.write(f"{label}=<error: {exc}>\n")

        try:
            source_path.write_text(driver.page_source, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"page_source_error={exc}\n")

        try:
            screenshot_saved = driver.get_screenshot_as_file(str(screenshot_path))
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"screenshot_error={exc}\n")

        meta_file.write(f"screenshot_saved={screenshot_saved}\n")
        meta_file.write(f"screenshot_path={screenshot_path}\n")
        meta_file.write(f"source_path={source_path}\n")


def capture_web_debug_state(driver, prefix: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    source_path = ARTIFACTS_DIR / f"{prefix}.html"
    meta_path = ARTIFACTS_DIR / f"{prefix}.txt"
    screenshot_path = ARTIFACTS_DIR / f"{prefix}.png"

    with meta_path.open("w", encoding="utf-8") as meta_file:
        for label, getter in (
            ("current_url", lambda: driver.current_url),
            ("title", lambda: driver.title),
            ("current_context", lambda: getattr(driver, "current_context", "")),
        ):
            try:
                meta_file.write(f"{label}={getter()}\n")
            except Exception as exc:  # pragma: no cover - debug helper only
                meta_file.write(f"{label}=<error: {exc}>\n")

        try:
            source_path.write_text(driver.page_source, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - debug helper only
            meta_file.write(f"page_source_error={exc}\n")

        try:
            screenshot_saved = driver.get_screenshot_as_file(str(screenshot_path))
        except Exception as exc:  # pragma: no cover - debug helper only
            screenshot_saved = False
            meta_file.write(f"screenshot_error={exc}\n")

        meta_file.write(f"screenshot_saved={screenshot_saved}\n")
        meta_file.write(f"screenshot_path={screenshot_path}\n")
        meta_file.write(f"source_path={source_path}\n")
