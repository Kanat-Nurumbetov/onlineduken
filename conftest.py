from appium import webdriver
from appium.options.android import UiAutomator2Options
import pytest
from pathlib import Path
import os
from dotenv import load_dotenv
import allure
from selenium.common.exceptions import WebDriverException
import re

from core import waits
from core.textfinder import TextFinder
from screens.login_screen import LoginScreen
from core.qr_generator import QrGenerator
from core.device_media import push_png_via_driver
from core.gallery_cleaner import clean_gallery

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "config" / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    raise RuntimeError(f"Не найден config/.env по пути: {ENV_PATH}")

def resolve_app_path() -> str:
    raw = os.getenv("APP_PATH", "").strip()
    if not raw:
        raise RuntimeError("APP_PATH пуст в config/.env")

    p = Path(raw)
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()

    if not p.exists():
        raise FileNotFoundError(f"APK не найден: {p}")

    return str(p)

def appium_options():
    opts = UiAutomator2Options()
    opts.set_capability('platformName','Android')
    opts.set_capability('deviceName', 'emulator-5554')
    opts.set_capability('udid', 'emulator-5554')
    opts.set_capability('platformVersion', '11.0')
    opts.set_capability('automationName', 'UiAutomator2')
    opts.set_capability('appium:appPackage', 'kz.halyk.onlinebank.stage')
    opts.set_capability('appium:appActivity', 'kz.halyk.onlinebank.ui_release4.screens.auth.AuthActivity')
    opts.set_capability('app', resolve_app_path())
    opts.set_capability('autoGrantPermissions', True)
    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability("appium:relaxed-security", 'deny-insecure')
    return opts

def _slug(nodeid: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', nodeid)

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

@pytest.fixture
def driver(request):
    driver = webdriver.Remote('http://127.0.0.1:4723', options=appium_options())

    yield driver

    failed = any(
        getattr(request.node, f"rep_{stage}", None) and getattr(request.node, f"rep_{stage}").failed
        for stage in ("setup", "call", "teardown")
    )
    if failed:
        try:
            png = driver.get_screenshot_as_png()
            allure.attach(
                png,
                name=_slug(request.node.nodeid) + "_screenshot",
                attachment_type=allure.attachment_type.PNG
            )
        except WebDriverException:
            pass

    driver.quit()

@pytest.fixture
def text_finder(driver):
    waits_obj = waits.Waits(driver)
    return TextFinder(driver, waits_obj)

@pytest.fixture
def login(driver):
    login = LoginScreen(driver)
    login.phone_enter("7771112222")
    login.login_click()
    login.confirmation_code_enter("123456")
    login.quik_pin_setup()
    login.quik_pin_setup()
    login.geo_permission()
    login.online_duken()
    return login

@pytest.fixture
def qr_png_on_device(driver, request):
    kind = getattr(request, "param", None)  # можно параметризовать через indirect
    gen = QrGenerator()
    # если тест параметризует kind напрямую, просто передай его
    path = gen.png(kind or "megapolis")
    device_path = push_png_via_driver(driver, path)   # /sdcard/Pictures/...
    return {"name": path.stem, "local": path, "device": device_path}

@pytest.fixture
def clean_gallery_before_test(driver):
    """
    Полная очистка галереи:
      - Android: чистим /sdcard/DCIM и /sdcard/Pictures
      - iOS симулятор: simctl erase (нужен UDID / booted)
    """
    ios_udid = os.getenv("IOS_SIM_UDID")  # задай в CI/локально, если нужна iOS
    clean_gallery(driver, ios_udid=ios_udid, only_test_album=None)
    yield