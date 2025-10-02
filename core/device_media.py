import base64
import os
import subprocess
from pathlib import Path


def push_png_via_driver(driver, local_path: Path, device_dir="/sdcard/Pictures/OnlineDuken") -> str:
    """Переносит PNG на устройство."""
    local_path = Path(local_path)
    platform = driver.capabilities.get("platformName", "").lower()

    if platform == "android":
        device_path = f"{device_dir}/{local_path.name}"
        driver.execute_script("mobile: shell", {"command": "mkdir", "args": ["-p", device_dir]})
        driver.push_file(device_path, base64.b64encode(local_path.read_bytes()).decode())
        driver.execute_script("mobile: shell", {
            "command": "am",
            "args": ["broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{device_path}"],
        })
        return device_path

    if platform == "ios":
        udid = driver.capabilities.get("udid", "booted")
        subprocess.run(["xcrun", "simctl", "addmedia", udid, str(local_path)], check=True)
        return f"photos://{local_path.name}"

    raise ValueError(f"Неподдерживаемая платформа: {platform}")