import base64
import os
import subprocess
from pathlib import Path


def push_png_via_driver(driver, local_path: Path, device_dir="/sdcard/Pictures/OnlineDuken") -> str:
    """Переносит PNG-файл на устройство в зависимости от платформы."""

    local_path = Path(local_path)
    platform = (driver.capabilities.get("platformName") or "").lower()

    if platform.startswith("android"):
        device_path = f"{device_dir}/{local_path.name}"

        driver.execute_script("mobile: shell", {"command": "mkdir", "args": ["-p", device_dir]})
        driver.push_file(device_path, base64.b64encode(local_path.read_bytes()).decode("ascii"))
        driver.execute_script("mobile: shell", {
            "command": "am",
            "args": [
                "broadcast",
                "-a",
                "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d",
                f"file://{device_path}",
            ],
        })
        return device_path

    if platform.startswith("ios"):
        is_simulator = bool(driver.capabilities.get("isSimulator", True))
        if not is_simulator:
            raise NotImplementedError(
                "Загрузка медиа на реальное iOS устройство не поддерживается — используйте симулятор или ручной аплоад"
            )

        udid = driver.capabilities.get("udid") or os.getenv("IOS_SIM_UDID", "booted")
        try:
            subprocess.run(["xcrun", "simctl", "addmedia", udid, str(local_path)], check=True)
        except FileNotFoundError as exc:
            raise RuntimeError("Команда 'xcrun' недоступна. Установите Xcode Command Line Tools") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Не удалось добавить файл в медиатеку симулятора: {exc}") from exc

        return f"photos://{local_path.name}"

    raise ValueError(f"Неподдерживаемая платформа для загрузки PNG: {platform}")
