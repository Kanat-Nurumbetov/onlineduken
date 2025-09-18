from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
import pytest
from pathlib import Path
import os
from dotenv import load_dotenv
import allure
from selenium.common.exceptions import WebDriverException
import re
import subprocess
import time
import requests
from typing import Dict, Any

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


def resolve_app_path(platform: str = "android") -> str:
    """Получение пути к приложению в зависимости от платформы"""
    env_key = f"{platform.upper()}_APP_PATH"
    raw = os.getenv(env_key, os.getenv("APP_PATH", "")).strip()

    if not raw:
        raise RuntimeError(f"{env_key} или APP_PATH пуст в config/.env")

    p = Path(raw)
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Приложение не найдено: {p}")

    return str(p)


def get_appium_url(platform: str) -> str:
    """Получение URL Appium сервера для платформы"""
    # Проверяем переменные окружения для Docker/Kubernetes
    if platform.lower() == "android":
        # В параллельном режиме Android всегда на порту 4723
        docker_url = os.getenv('ANDROID_APPIUM_URL', os.getenv('APPIUM_ANDROID_URL'))
        if docker_url:
            return docker_url
        host = os.getenv('ANDROID_APPIUM_HOST', '127.0.0.1')
        port = os.getenv('ANDROID_APPIUM_PORT', '4723')
    elif platform.lower() == "ios":
        # В параллельном режиме iOS всегда на порту 4724
        docker_url = os.getenv('IOS_APPIUM_URL', os.getenv('APPIUM_IOS_URL'))
        if docker_url:
            return docker_url
        host = os.getenv('IOS_APPIUM_HOST', '127.0.0.1')
        port = os.getenv('IOS_APPIUM_PORT', '4724')
    else:
        raise ValueError(f"Неподдерживаемая платформа: {platform}")

    return f'http://{host}:{port}'


def android_options() -> UiAutomator2Options:
    """Настройки для Android"""
    opts = UiAutomator2Options()
    opts.set_capability('platformName', 'Android')
    opts.set_capability('deviceName', os.getenv('ANDROID_DEVICE_NAME', 'emulator-5554'))
    opts.set_capability('udid', os.getenv('ANDROID_UDID', 'emulator-5554'))
    opts.set_capability('platformVersion', os.getenv('ANDROID_VERSION', '11.0'))
    opts.set_capability('automationName', 'UiAutomator2')
    opts.set_capability('appium:appPackage', 'kz.halyk.onlinebank.stage')
    opts.set_capability('appium:appActivity', 'kz.halyk.onlinebank.ui_release4.screens.auth.AuthActivity')
    opts.set_capability('app', resolve_app_path('android'))
    opts.set_capability('autoGrantPermissions', True)
    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability('appium:newCommandTimeout', 300)

    # Дополнительные настройки для CI/CD
    if os.getenv('CI'):
        opts.set_capability('appium:androidInstallTimeout', 90000)

    return opts


def ios_options() -> XCUITestOptions:
    """Настройки для iOS"""
    opts = XCUITestOptions()
    opts.set_capability('platformName', 'iOS')
    opts.set_capability('deviceName', os.getenv('IOS_DEVICE_NAME', 'iPhone 13'))
    opts.set_capability('platformVersion', os.getenv('IOS_VERSION', '15.0'))
    opts.set_capability('automationName', 'XCUITest')
    opts.set_capability('app', resolve_app_path('ios'))
    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability('appium:newCommandTimeout', 300)

    # UDID устройства/симулятора
    udid = os.getenv('IOS_UDID')
    if udid:
        opts.set_capability('udid', udid)

    return opts


def get_platform_from_pytest_args() -> str:
    """Определение платформы из аргументов pytest"""
    import sys

    # Проверяем аргументы командной строки
    for arg in sys.argv:
        if arg.startswith('--platform='):
            return arg.split('=')[1].lower()

    # Проверяем переменную окружения
    return os.getenv('TEST_PLATFORM', 'android').lower()


def wait_for_appium(host="127.0.0.1", port=4723, timeout=60):
    """Ожидание запуска Appium сервера"""
    url = f"http://{host}:{port}/status"
    for _ in range(timeout):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def ensure_emulator_running():
    """Проверка и запуск эмулятора если необходимо"""
    try:
        # Проверяем подключенные устройства
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if 'emulator-5554' in result.stdout and 'device' in result.stdout:
            return True
    except subprocess.CalledProcessError:
        pass

    # Если эмулятор не запущен, пытаемся его запустить
    avd_name = os.getenv('ANDROID_AVD_NAME', 'test_emulator')
    try:
        subprocess.Popen([
            'emulator', '-avd', avd_name, '-no-window', '-no-audio'
        ])
        # Ждем запуска
        subprocess.run(['adb', 'wait-for-device'], timeout=300)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _slug(nodeid: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', nodeid)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="session")
def test_platform():
    """Определение платформы для тестирования"""
    return get_platform_from_pytest_args()


@pytest.fixture(scope="session", params=["android", "ios"])
def multi_platform(request):
    """Параметризованная фикстура для многоплатформенного тестирования"""
    platform = request.param

    # Пропускаем iOS тесты если не на macOS (кроме случаев с удаленным устройством)
    if platform == "ios" and os.uname().sysname != "Darwin":
        if not os.getenv('IOS_REMOTE_URL'):
            pytest.skip("iOS тесты требуют macOS или удаленное iOS устройство")

    return platform


def _resolve_appium_endpoint(platform: str) -> tuple[str, int]:
    platform = platform.lower()
    if platform == "android":
        host = os.getenv("ANDROID_APPIUM_HOST") or os.getenv("APPIUM_HOST", "127.0.0.1")
        port = int(os.getenv("ANDROID_APPIUM_PORT") or os.getenv("APPIUM_PORT", "4723"))
        return host, port
    if platform == "ios":
        host = os.getenv("IOS_APPIUM_HOST") or os.getenv("APPIUM_HOST", "127.0.0.1")
        port = int(os.getenv("IOS_APPIUM_PORT") or 4724)
        return host, port
    raise ValueError(f"Неподдерживаемая платформа для Appium: {platform}")


@pytest.fixture(scope="session")
def appium_service():
    """Гибко управляет Appium-серверами для разных платформ."""

    processes: dict[tuple[str, int], subprocess.Popen | None] = {}

    def ensure(platform: str):
        host, port = _resolve_appium_endpoint(platform)
        key = (host, port)

        if key in processes:
            # уже запущен/проверен
            return processes[key]

        external = os.getenv('APPIUM_EXTERNAL')
        if external:
            if not wait_for_appium(host, port):
                raise RuntimeError(f"Внешний Appium сервер недоступен по адресу {host}:{port}")
            processes[key] = None
            return None

        proc = subprocess.Popen([
            'appium',
            '--address', host,
            '--port', str(port),
            '--relaxed-security'
        ])

        if not wait_for_appium(host, port):
            proc.terminate()
            proc.wait()
            raise RuntimeError(f"Не удалось запустить Appium сервер на {host}:{port}")

        processes[key] = proc
        return proc

    yield ensure

    for proc in processes.values():
        if proc:
            proc.terminate()
            proc.wait()


@pytest.fixture
def driver(request, test_platform, appium_service):
    """Драйвер для указанной платформы"""
    # Инициализируем driver как None в самом начале
    driver = None
    platform = getattr(request, 'param', test_platform)

    # Предварительные проверки
    if platform.lower() == "android":
        options = android_options()
        if not ensure_emulator_running():
            pytest.skip("Android эмулятор недоступен")
    elif platform.lower() == "ios":
        options = ios_options()
        if os.uname().sysname != "Darwin" and not os.getenv('IOS_REMOTE_URL'):
            pytest.skip("iOS тесты требуют macOS или удаленное iOS устройство")
    else:
        pytest.skip(f"Неподдерживаемая платформа: {platform}")

    # Гарантируем наличие Appium сервера
    appium_service(platform)

    # Создаем драйвер только после всех проверок
    appium_url = get_appium_url(platform)

    try:
        driver = webdriver.Remote(appium_url, options=options)
        driver.test_platform = platform.lower()
    except Exception as e:
        pytest.skip(f"Не удалось подключиться к {platform} Appium серверу: {e}")

    # Yield должен быть в try-finally для гарантированной очистки
    try:
        yield driver
    finally:
        # Cleanup выполнится независимо от того, как завершился тест
        if driver is not None:
            # Скриншот при падении
            try:
                failed = any(
                    getattr(request.node, f"rep_{stage}", None) and
                    getattr(request.node, f"rep_{stage}").failed
                    for stage in ("setup", "call", "teardown")
                )

                if failed:
                    png = driver.get_screenshot_as_png()
                    screenshot_name = f"{_slug(request.node.nodeid)}_{platform}_screenshot"
                    allure.attach(
                        png,
                        name=screenshot_name,
                        attachment_type=allure.attachment_type.PNG
                    )
            except:
                pass  # Игнорируем ошибки скриншота

            # Закрываем драйвер
            try:
                driver.quit()
            except:
                pass  # Игнорируем ошибки закрытия


@pytest.fixture
def multi_driver(request, multi_platform):
    """Параметризованный драйвер для многоплатформенного тестирования"""

    request.param = multi_platform
    return request.getfixturevalue("driver")


# Платформо-специфичные фикстуры
@pytest.fixture
def android_driver(request):
    """Драйвер специально для Android"""

    request.param = "android"
    return request.getfixturevalue("driver")


@pytest.fixture
def ios_driver(request):
    """Драйвер специально для iOS"""

    if os.uname().sysname != "Darwin" and not os.getenv('IOS_REMOTE_URL'):
        pytest.skip("iOS тесты требуют macOS или удаленное iOS устройство")

    request.param = "ios"
    return request.getfixturevalue("driver")


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
    try:
        device_path = push_png_via_driver(driver, path)
    except NotImplementedError as exc:
        pytest.skip(str(exc))
    except RuntimeError as exc:
        pytest.skip(f"Не удалось загрузить QR на устройство: {exc}")
    return {"name": path.stem, "local": path, "device": device_path}


@pytest.fixture
def clean_gallery_before_test(driver):
    """Очистка галереи с учетом платформы"""
    platform = getattr(driver, 'test_platform', 'android')
    ios_udid = os.getenv("IOS_SIM_UDID") if platform == 'ios' else None
    clean_gallery(driver, ios_udid=ios_udid, only_test_album=None)
    yield
