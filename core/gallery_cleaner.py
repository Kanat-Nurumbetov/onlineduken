# core/gallery_cleaner.py
from __future__ import annotations
import os
import subprocess

def clean_gallery(driver, *, ios_udid: str | None = None, only_test_album: str | None = None) -> None:
    """
    Универсальная очистка медиагалереи перед тестом.

    - ANDROID (эмулятор/реал): через mobile:shell.
      Если передан only_test_album -> чистим только /sdcard/Pictures/<album>,
      иначе чистим ВСЁ: /sdcard/DCIM/* и /sdcard/Pictures/*.

    - iOS (ТОЛЬКО симулятор): через `xcrun simctl`. Нужен UDID симулятора.
      По умолчанию стираем весь симулятор (erase), что гарантированно убирает все фото.
      Это тяжёлая операция, но безопасная и стабильная для единственного теста.
    """
    platform = (driver.capabilities.get("platformName") or "").lower()

    if platform.startswith("android"):
        _clean_android(driver, only_test_album=only_test_album)
        return

    if platform.startswith("ios"):
        is_sim = bool(driver.capabilities.get("isSimulator", True))  # на симе часто True/1
        if not is_sim:
            # На реальном iOS-устройстве из теста корректно и безопасно стереть галерею нельзя.
            # Лучше пропустить или сделать no-op.
            return
        _clean_ios_simulator(ios_udid)
        return


def _clean_android(driver, *, only_test_album: str | None) -> None:
    # готовим команды
    if only_test_album:
        folder = f"/sdcard/Pictures/{only_test_album}"
        sh = f'rm -rf "{folder}"/* 2>/dev/null || true; mkdir -p "{folder}"'
        rescan_targets = [folder]
    else:
        sh = (
            'rm -rf /sdcard/DCIM/* /sdcard/Pictures/* 2>/dev/null || true; '
            'mkdir -p /sdcard/DCIM/Camera /sdcard/Pictures'
        )
        rescan_targets = ["/sdcard/DCIM", "/sdcard/Pictures"]

    # 1) удаляем файлы
    driver.execute_script("mobile: shell", {"command": "sh", "args": ["-c", sh]})

    # 2) перескан медиатеки
    # Начиная с новых Android есть команда cmd media rescan. Если не сработает — fallback.
    for path in rescan_targets:
        try:
            driver.execute_script("mobile: shell", {"command": "cmd", "args": ["media", "rescan", path]})
        except Exception:
            driver.execute_script("mobile: shell", {
                "command": "am",
                "args": ["broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_DIR", "-d", f"file://{path}"]
            })


def _clean_ios_simulator(udid: str | None) -> None:
    """
    Стираем содержимое симулятора (erase) — гарантированно чисто, в т.ч. фото/видео.
    Требуется macOS с установленными Xcode CLI tools. Работает ТОЛЬКО для симулятора.
    """
    if not _is_macos():
        # Ничего не делаем, если не macOS (например, тесты под Android на Windows).
        return

    target = udid or "booted"
    # shutdown (на всякий), erase и boot
    subprocess.run(["xcrun", "simctl", "shutdown", target], check=False)
    subprocess.run(["xcrun", "simctl", "erase", target],    check=True)
    subprocess.run(["xcrun", "simctl", "boot", target],     check=True)


def _is_macos() -> bool:
    return os.name == "posix" and "darwin" in os.uname().sysname.lower()
