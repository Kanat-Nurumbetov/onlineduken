from contextlib import suppress
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from pathlib import Path
import os, re, pytest
from dotenv import load_dotenv
import allure
import subprocess
import time
import requests
import uuid

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
    return v.strip().lower() in ("1","true","yes","y","on")

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

def android_options(idx: int) -> UiAutomator2Options:
    opts = UiAutomator2Options()
    udids = [u.strip() for u in os.getenv('ANDROID_UDIDS','emulator-5554').split(',') if u.strip()]
    if idx >= len(udids):
        pytest.skip(f"Нет свободного Android-устройства для воркера #{idx}")
    udid = udids[idx]

    opts.set_capability('platformName', 'Android')
    opts.set_capability('udid', udid)
    opts.set_capability('deviceName', udid)

    # уникальные порты
    opts.set_capability('systemPort', 8200 + idx)
    opts.set_capability('chromeDriverPort', 11000 + idx)
    opts.set_capability('mjpegServerPort', 7810 + idx)

    # автозапуск соответствующего AVD (по списку)
    avd_names = [a.strip() for a in os.getenv('ANDROID_AVD_NAMES','').split(',') if a.strip()]
    if idx < len(avd_names):
        opts.set_capability('avd', avd_names[idx])
        headless = env_bool('ANDROID_HEADLESS', False)
        avd_args = ['-no-snapshot-load', '-no-snapshot-save']
        # Графика: в headless режиме безопаснее swiftshader
        avd_args += ['-gpu', 'swiftshader_indirect' if headless else 'angle']
        if headless:
            avd_args += ['-no-window', '-no-audio']
        opts.set_capability('avdArgs', ' '.join(avd_args))
        opts.set_capability('avdLaunchTimeout', 120000)
        opts.set_capability('avdReadyTimeout', 120000)

    # дальше — твои cap'ы приложения
    opts.set_capability('automationName', 'UiAutomator2')
    opts.set_capability('appium:appPackage', 'kz.halyk.onlinebank.stage')
    opts.set_capability('appium:appActivity', 'kz.halyk.onlinebank.ui_release4.screens.auth.AuthActivity')
    opts.set_capability('app', resolve_app_path('android'))
    opts.set_capability('autoGrantPermissions', True)
    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability('appium:newCommandTimeout', 300)
    return opts

def ios_options(idx: int) -> XCUITestOptions:
    opts = XCUITestOptions()
    opts.set_capability('platformName','iOS')
    opts.set_capability('automationName','XCUITest')

    udids = [u.strip() for u in os.getenv('IOS_UDIDS','').split(',') if u.strip()]
    if udids:
        if idx >= len(udids):
            pytest.skip(f"Нет свободного iOS-устройства для воркера #{idx}")
        opts.set_capability('udid', udids[idx])

    opts.set_capability('wdaLocalPort', 8100 + idx)
    opts.set_capability('webkitDebugProxyPort', 27753 + idx)

    opts.set_capability('deviceName', os.getenv('IOS_DEVICE_NAME','iPhone 13'))
    opts.set_capability('platformVersion', os.getenv('IOS_VERSION','15.0'))
    opts.set_capability('app', resolve_app_path('ios'))
    opts.set_capability('autoAcceptAlerts', True)
    opts.set_capability('appium:newCommandTimeout', 300)
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


@pytest.fixture(scope="session", params=(
    ["android", "ios"] if os.getenv("ENABLE_MULTI_PLATFORM", "0").strip().lower() in ("1","true","yes","y","on")
    else [os.getenv('TEST_PLATFORM', 'android').lower()]
))
def multi_platform(request):
    """Параметризованная фикстура для многоплатформенного тестирования.

    По умолчанию не множит сессию: берёт платформу из --platform/TEST_PLATFORM.
    Для прогона обеих платформ установите ENABLE_MULTI_PLATFORM=1.
    """
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
    processes: dict[tuple[str,int], subprocess.Popen|None] = {}

    def ensure(platform: str):
        host, port = _resolve_appium_endpoint(platform)
        key = (host, port)
        if key in processes:
            return processes[key]

        if env_bool('APPIUM_EXTERNAL', False):
            if not wait_for_appium(host, port):
                raise RuntimeError(f"Внешний Appium сервер недоступен по адресу {host}:{port}")
            processes[key] = None
            return None

        proc = subprocess.Popen(['appium','--address', host,'--port', str(port),'--relaxed-security'])
        if not wait_for_appium(host, port):
            proc.terminate(); proc.wait()
            raise RuntimeError(f"Не удалось запустить Appium сервер на {host}:{port}")
        processes[key] = proc
        return proc

    yield ensure

    for proc in processes.values():
        if proc:
            proc.terminate(); proc.wait()


@pytest.fixture
def driver(request, test_platform, appium_service):
    drv = None
    idx = worker_index(request.config)
    platform = getattr(request, 'param', test_platform).lower()

    # гарантируем сервер
    appium_service(platform)
    appium_url = get_appium_url(platform)

    # подготовим устройство
    if platform == "android":
        # (опционально) автозапуск нужного AVD для этого UDID/порта
        drv_opts = android_options(idx)
    elif platform == "ios":
        drv_opts = ios_options(idx)
    else:
        pytest.skip(f"Неподдерживаемая платформа: {platform}")

    attempts = int(os.getenv("APPIUM_CONNECT_RETRIES", "3") or 3)
    delay = float(os.getenv("APPIUM_CONNECT_RETRY_DELAY", "2") or 2)
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            drv = webdriver.Remote(appium_url, options=drv_opts)
            drv.test_platform = platform
            drv.worker_index = idx
            break
        except Exception as e:
            last_error = e
            if attempt < attempts:
                time.sleep(delay)
            else:
                pytest.skip(f"Не удалось подключиться к {platform} Appium серверу после {attempts} попыток: {e}")

    try:
        yield drv
    finally:
        if drv:
            try:
                failed = any(
                    getattr(request.node, f"rep_{stage}", None) and
                    getattr(request.node, f"rep_{stage}").failed
                    for stage in ("setup","call","teardown")
                )
                if failed:
                    png = drv.get_screenshot_as_png()
                    allure.attach(png, name=f"{_slug(request.node.nodeid)}_{platform}_screenshot",
                                  attachment_type=allure.attachment_type.PNG)
            except:
                pass
            with suppress(Exception):
                drv.quit()


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

def _worker_album(request) -> str:
    return f"OnlineDuken_{worker_id(request.config)}"

@pytest.fixture
def qr_png_on_device(driver, request):
    kind = getattr(getattr(request.node, "callspec", None), "params", {}).get("kind")
    album = _worker_album(request)
    gen = QrGenerator()
    # уникальное имя
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
