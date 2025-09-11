import base64
from pathlib import Path

def push_png_via_driver(driver, local_path: Path, device_dir="/sdcard/Pictures/OnlineDuken") -> str:
    local_path = Path(local_path)
    device_path = f"{device_dir}/{local_path.name}"

    driver.execute_script("mobile: shell", {"command": "mkdir", "args": ["-p", device_dir]})
    driver.push_file(device_path, base64.b64encode(local_path.read_bytes()).decode("ascii"))
    driver.execute_script("mobile: shell", {
        "command": "am",
        "args": ["broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE","-d", f"file://{device_path}"]
    })
    return device_path
