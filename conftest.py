from contextlib import suppress
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from pathlib import Path
import os, re, pytest
from dotenv import load_dotenv
import subprocess
import time
import requests
import uuid
from selenium.common.exceptions import WebDriverException

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


def env_bool(name: str, default=False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def worker_id(config) -> str:
    wi = getattr(config, "workerinput", None)
    return (wi or {}).get("workerid", "gw0")


def worker_index(config) -> int:
    wid = worker_id(config)
    m = re.match(r"gw(\d+)", wid)
    return int(m.group(1)) if m else 0


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
    """Получение URL Appium сервера (поддержка Docker/K8s/локального окружения)"""
    platform = platform.lower()

    if platform == "android":
        # Приоритет: Docker URL > отдельные переменные > localhost
        docker_url = os.getenv('ANDROID_APPIUM_URL', os.getenv('APPIUM_ANDROID_URL'))
        if docker_url:
            return docker_url
        host = os.getenv('ANDROID_APPIUM_HOST', os.getenv('APPIUM_HOST', '127.0.0.1'))
        port = os.getenv('ANDROID_APPIUM_PORT', os.getenv('APPIUM_PORT', '4723'))

    elif platform == "ios":
        docker_url = os.getenv('IOS_APPIUM_URL', os.getenv('APPIUM_IOS_URL'))
        if docker_url:
            return docker_url
        host = os.getenv('IOS_APPIUM_HOST', os.getenv('APPIUM_HOST', '127.0.0.1'))
        port = os.getenv('IOS_APPIUM_PORT', '4724')

    else:
        raise ValueError(f"Неподдерживаемая платформа: {platform}")

    return f'http://{host}:{port}'


def get_device_name(platform: str = "android") -> str:
    """Получение имени устройства с поддержкой Docker"""
    if platform.lower() == "android":
        # В Docker: DEVICE_HOST задаёт хост контейнера эмулятора
        device_host = os.getenv("DEVICE_HOST")
        if device_host:
            return f"{device_host}:5555"
        return os.getenv("DEVICE_NAME", "emulator-5554")
    else:
        return os.getenv("IOS_DEVICE_NAME", "iPhone 13")


def wait_for_appium(url: str, timeout: int = 60) -> bool:
    """Ожидание запуска Appium сервера"""
    status_url = f"{url}/status"
    for _ in range(timeout):
        try:
            response = requests.get(status_url, timeout=1)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def android_options(idx: int = 0) -> UiAutomator2Options:
    """Конфигурация Android с поддержкой параллельного запуска и CI/CD"""
    opts = UiAutomator2Options()

    # UDID устройства
    udids = [u.strip() for u in os.getenv('ANDROID_UDIDS', 'emulator-5554').split(',') if u.strip()]
    if idx >= len(udids):
        pytest.skip(f"Нет свободного Android-устройства для воркера #{idx}")
    udid = udids[idx]

    opts.set_capability('platformName', 'Android')
    opts.set_capability('udid', udid)
    opts.set_capability('deviceName', get_device_name('android'))

    # Уникальные порты для параллельного запуска
    opts.set_capability('systemPort', 8200 + idx)
    opts.set_capability('chromeDriverPort', 11000 + idx)
    opts.set_capability('mjpegServerPort', 7810 + idx)

    # AVD настройки (для локального окружения)
    avd_names = [a.strip() for a in os.getenv('ANDROID_AVD_NAMES', '').split(',') if a.strip()]
    if avd_names and idx < len(avd_names):
        opts.set_capability('avd', avd_names[idx])
        headless = env_bool('ANDROID_HEADLESS', False)
        avd_args = ['-no-snapshot-load', '-no-snapshot-save']
        avd_args += ['-gpu', 'swiftshader_indirect' if headless else 'angle']
        if headless:
            avd_args += ['-no-window', '-no-audio']
        opts.set_capability('avdArgs', ' '.join(avd_args))
        opts.set_capability('avdLaunchTimeout', 120000)
        opts.set_capability('avdReadyTimeout', 120000)

    # Приложение
    opts.set_capability('automationName', 'UiAutomator2')
    opts.set_capability('appium:appPackage', 'kz.halyk.onlinebank.stage')
    opts.set_capability('appium:appActivity', 'kz.halyk.onlinebank.ui_release4.screens.auth.AuthActivity')

    # Путь к APK (опционально, если не установлен)
    if os.getenv('ANDROID_APP_PATH'):
        opts.set_capability('app', resolve_app_path('android'))

    # Разрешения
    opts.set_capability('autoGrantPermissions', True)
    opts.set_capability('autoAcceptAlerts', True)

    # Таймауты для стабильности в CI/CD
    opts.set_capability('newCommandTimeout', 300)
    opts.set_capability('uiautomator2ServerLaunchTimeout', 90000)
    opts.set_capability('uiautomator2ServerInstallTimeout', 90000)
    opts.set_capability('adbExecTimeout', 60000)
    opts.set_capability('androidInstallTimeout', 120000)
    opts.set_capability('ignoreHiddenApiPolicyError', True)
    opts.set_capability('disableWindowAnimation', True)

    return opts


def ios_options(idx: int = 0) -> XCUITestOptions:
    """Конфигурация iOS с поддержкой параллельного запуска"""
    opts = XCUITestOptions()
    opts.set_capability('platformName', 'iOS')
    opts.set_capability('automationName', 'XCUITest')

    udids = [u.strip() for u in os.getenv('IOS_UDIDS', '').split(',') if u.strip()]
    if udids:
        if idx >= len(udids):
            pytest.skip(f"Нет свободного iOS-устройства для воркера #{idx}")
        opts.set_capability('udid', udids[idx])

    opts.set_capability('wdaLocalPort', 8100 + idx)
    opts.set_capability('webkitDebugProxyPort', 27753 + idx)

    opts.set_capability('deviceName', get_device_name('ios'))
    opts.set_capability('platformVersion', os.getenv('IOS_VERSION', '15.0'))

    if os.getenv('IOS_APP_PATH'):
        opts.set_capability('app', resolve_app_path('ios'))

    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability('newCommandTimeout', 300)
    return opts


def get_platform_from_pytest_args() -> str:
    """Определение платформы из аргументов pytest"""
    import sys
    for arg in sys.argv:
        if arg.startswith('--platform='):
            return arg.split('=')[1].lower()
    return os.getenv('TEST_PLATFORM', 'android').lower()


def _slug(nodeid: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', nodeid)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "delayed(seconds=20): задержать старт конкретного теста/параметра"
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    m = item.get_closest_marker("delayed")
    if m:
        seconds = int(m.kwargs.get("seconds") or (m.args[0] if m.args else 20))
        time.sleep(seconds)


@pytest.fixture(scope="session")
def test_platform():
    """Определение платформы для тестирования"""
    return get_platform_from_pytest_args()


@pytest.fixture(scope="session", params=(
        ["android", "ios"] if env_bool("ENABLE_MULTI_PLATFORM")
        else [os.getenv('TEST_PLATFORM', 'android').lower()]
))
def multi_platform(request):
    """Параметризованная фикстура для многоплатформенного тестирования"""
    platform = request.param

    if platform == "ios" and os.uname().sysname != "Darwin":
        if not os.getenv('IOS_REMOTE_URL'):
            pytest.skip("iOS тесты требуют macOS или удаленное iOS устройство")

    return platform


@pytest.fixture(scope="session", autouse=True)
def check_environment():
    """Проверка окружения перед запуском тестов"""
    platform = os.getenv('TEST_PLATFORM', 'android').lower()
    appium_url = get_appium_url(platform)

    # В Docker/CI окружении пропускаем локальные проверки
    if env_bool("CI") or env_bool("DOCKER_ENV"):
        print("🐳 Docker/CI окружение обнаружено")
        print(f"📍 Appium URL: {appium_url}")
        return

    # Локальные проверки
    if not env_bool('APPIUM_EXTERNAL'):
        print("⚠️ Запуск в локальном режиме. Убедитесь что Appium и эмулятор запущены.")
        print(f"📍 Ожидаемый Appium URL: {appium_url}")

    try:
        response = requests.get(f"{appium_url}/status", timeout=5)
        if response.status_code != 200:
            pytest.skip(f"❌ Appium не отвечает на {appium_url}")
        print("✅ Appium доступен")
    except Exception as e:
        pytest.skip(f"❌ Не удалось подключиться к Appium: {e}")

    print("✅ Окружение готово к тестированию")


@pytest.fixture(scope="session")
def appium_service():
    """Управление жизненным циклом Appium сервера (только для локального окружения)"""
    processes: dict[str, subprocess.Popen | None] = {}

    def ensure(platform: str):
        # В Docker/CI всегда используем внешний Appium
        if env_bool('CI') or env_bool('DOCKER_ENV') or env_bool('APPIUM_EXTERNAL'):
            url = get_appium_url(platform)
            if not wait_for_appium(url, timeout=30):
                raise RuntimeError(f"Внешний Appium недоступен: {url}")
            return None

        # Локальный запуск Appium
        url = get_appium_url(platform)
        if url in processes:
            return processes[url]

        host = url.split("://")[1].split(":")[0]
        port = url.split(":")[-1]

        proc = subprocess.Popen([
            'appium',
            '--address', host,
            '--port', port,
            '--relaxed-security'
        ])

        if not wait_for_appium(url, timeout=60):
            proc.terminate()
            proc.wait()
            raise RuntimeError(f"Не удалось запустить Appium: {url}")

        processes[url] = proc
        return proc

    yield ensure

    # Останавливаем только локально запущенные процессы
    for proc in processes.values():
        if proc:
            proc.terminate()
            proc.wait()


@pytest.fixture(scope="module")
def driver(request, appium_service, multi_platform):
    """Универсальный драйвер с поддержкой Docker, CI/CD и локального окружения"""
    platform = multi_platform
    idx = worker_index(request.config)

    # Запускаем/проверяем Appium
    appium_service(platform)

    # Получаем опции в зависимости от платформы
    if platform == "android":
        options = android_options(idx)
    elif platform == "ios":
        options = ios_options(idx)
    else:
        pytest.skip(f"Неподдерживаемая платформа: {platform}")

    appium_url = get_appium_url(platform)

    max_retries = 3
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            print(f"🔄 Подключение к Appium: {appium_url} ({platform}) - попытка {attempt + 1}/{max_retries}")
            driver = webdriver.Remote(appium_url, options=options)
            driver.test_platform = platform
            print(f"✅ Успешное подключение к Appium ({platform})")
            yield driver
            driver.quit()
            return

        except WebDriverException as e:
            error_msg = str(e)
            print(f"⚠️ Ошибка подключения: {error_msg[:200]}")

            if "instrumentation process cannot be initialized" in error_msg.lower():
                print("💡 Совет: Проверьте что приложение не крашится при запуске")

            if attempt < max_retries - 1:
                print(f"⏳ Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)

                # Попытка перезапуска приложения через ADB (только Android)
                if platform == "android":
                    try:
                        subprocess.run(
                            ["adb", "shell", "am", "force-stop", "kz.halyk.onlinebank.stage"],
                            timeout=10
                        )
                        time.sleep(2)
                    except:
                        pass
            else:
                pytest.skip(f"❌ Не удалось подключиться после {max_retries} попыток: {error_msg[:300]}")


@pytest.fixture
def android_driver(request, appium_service):
    """Драйвер специально для Android"""
    idx = worker_index(request.config)
    appium_service("android")

    options = android_options(idx)
    appium_url = get_appium_url("android")

    driver = webdriver.Remote(appium_url, options=options)
    driver.test_platform = "android"
    yield driver
    driver.quit()


@pytest.fixture
def ios_driver(request, appium_service):
    """Драйвер специально для iOS"""
    if os.uname().sysname != "Darwin" and not os.getenv('IOS_REMOTE_URL'):
        pytest.skip("iOS тесты требуют macOS или удаленное iOS устройство")

    idx = worker_index(request.config)
    appium_service("ios")

    options = ios_options(idx)
    appium_url = get_appium_url("ios")

    driver = webdriver.Remote(appium_url, options=options)
    driver.test_platform = "ios"
    yield driver
    driver.quit()


@pytest.fixture(scope="module")
def login(driver):
    """Логин выполняется один раз для модуля"""
    login_screen = LoginScreen(driver)

    # Данные из переменных окружения
    phone = os.getenv("TEST_PHONE", "7771112222")
    code = os.getenv("TEST_CODE", "123456")

    try:
        login_screen.phone_enter(phone)
        login_screen.login_click()
        login_screen.confirmation_code_enter(code)
        login_screen.quik_pin_setup()
        login_screen.quik_pin_setup()
        login_screen.geo_permission()
        login_screen.online_duken()
        print("✅ Логин выполнен успешно")
    except Exception as e:
        pytest.skip(f"❌ Ошибка логина: {e}")

    return login_screen


# ============ Function fixtures ============
def _worker_album(request) -> str:
    return f"OnlineDuken_{worker_id(request.config)}"


@pytest.fixture
def qr_png_on_device(driver, request):
    """Генерация и загрузка QR-кода на устройство"""
    kind = getattr(getattr(request.node, "callspec", None), "params", {}).get("kind")
    album = _worker_album(request)
    gen = QrGenerator()
    name = f"{kind}_{uuid.uuid4().hex[:6]}"
    path = gen.png(kind, filename=f"{name}.png")

    try:
        device_dir = f"/sdcard/Pictures/{album}"
        device_path = push_png_via_driver(driver, path, device_dir=device_dir)
    except NotImplementedError as exc:
        pytest.skip(str(exc))
    except RuntimeError as exc:
        pytest.skip(f"Не удалось загрузить QR на устройство: {exc}")

    return {"album": album, "name": name, "local": path, "device": device_path}


@pytest.fixture
def clean_gallery_before_test(driver, request):
    """Очистка галереи с учетом платформы"""
    platform = getattr(driver, 'test_platform', 'android')
    ios_udid = os.getenv("IOS_SIM_UDID") if platform == 'ios' else None
    album = _worker_album(request)
    clean_gallery(driver, ios_udid=ios_udid, only_test_album=album)
    yield