from __future__ import annotations

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.common.base import AppiumOptions
from appium.options.ios import XCUITestOptions
from appium.webdriver.client_config import AppiumClientConfig

from mobile_automation.config import Settings


def _browserstack_common_caps(settings: Settings, session_name: str) -> dict:
    return {
        "projectName": settings.browserstack_project_name,
        "buildName": settings.browserstack_build_name,
        "sessionName": session_name,
        "appiumVersion": "2.19.0",
        "debug": True,
        "networkLogs": True,
    }


def _browserstack_client_config(settings: Settings) -> AppiumClientConfig:
    return AppiumClientConfig(
        remote_server_addr=settings.browserstack_hub_url,
        username=settings.browserstack_username,
        password=settings.browserstack_access_key,
        timeout=300,
    )


def _android_local_options(settings: Settings) -> UiAutomator2Options:
    settings.require(("ANDROID_APP_PATH", settings.android_app_path))
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = settings.android_udid or settings.android_device_name
    options.set_capability("appium:app", settings.android_app_path)
    options.set_capability("appium:autoGrantPermissions", True)
    options.set_capability("appium:adbExecTimeout", 180000)
    options.set_capability("appium:newCommandTimeout", 240)
    # Optional: preserve app data between Appium sessions. See Settings.appium_no_reset.
    # We intentionally do NOT set dontStopAppOnReset — letting Appium stop the
    # app cleanly avoids the UIAutomator2 bridge wedging when the previous
    # process is left around.
    if settings.appium_no_reset:
        options.set_capability("appium:noReset", True)
        options.set_capability("appium:fullReset", False)
    if settings.android_udid:
        options.udid = settings.android_udid
        options.set_capability("appium:udid", settings.android_udid)
    if settings.android_app_package:
        options.set_capability("appium:appPackage", settings.android_app_package)
    if settings.android_app_activity:
        options.set_capability("appium:appActivity", settings.android_app_activity)
    if settings.android_platform_version:
        options.platform_version = settings.android_platform_version
    return options


def _android_browserstack_options(settings: Settings, session_name: str) -> UiAutomator2Options:
    settings.require(
        ("BROWSERSTACK_USERNAME", settings.browserstack_username),
        ("BROWSERSTACK_ACCESS_KEY", settings.browserstack_access_key),
        ("BROWSERSTACK_APP_ANDROID", settings.browserstack_app_android),
    )
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.set_capability("appium:app", settings.browserstack_app_android)
    options.set_capability("appium:autoGrantPermissions", True)
    options.set_capability("appium:newCommandTimeout", 240)
    options.set_capability(
        "bstack:options",
        {
            **_browserstack_common_caps(settings, session_name),
            "deviceName": settings.browserstack_android_device,
            "platformVersion": settings.browserstack_android_os_version,
            "appiumLogs": True,
            "deviceLogs": True,
        },
    )
    return options


def _ios_local_options(settings: Settings) -> XCUITestOptions:
    settings.require(("IOS_APP_PATH", settings.ios_app_path))
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.automation_name = "XCUITest"
    options.device_name = settings.ios_device_name
    options.set_capability("appium:app", settings.ios_app_path)
    options.set_capability("appium:newCommandTimeout", 240)
    if settings.ios_platform_version:
        options.platform_version = settings.ios_platform_version
    if settings.ios_bundle_id:
        options.set_capability("appium:bundleId", settings.ios_bundle_id)
    return options


def _ios_browserstack_options(settings: Settings, session_name: str) -> XCUITestOptions:
    settings.require(
        ("BROWSERSTACK_USERNAME", settings.browserstack_username),
        ("BROWSERSTACK_ACCESS_KEY", settings.browserstack_access_key),
        ("BROWSERSTACK_APP_IOS", settings.browserstack_app_ios),
    )
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.automation_name = "XCUITest"
    options.set_capability("appium:app", settings.browserstack_app_ios)
    options.set_capability("appium:newCommandTimeout", 240)
    options.set_capability(
        "bstack:options",
        {
            **_browserstack_common_caps(settings, session_name),
            "deviceName": settings.browserstack_ios_device,
            "platformVersion": settings.browserstack_ios_os_version,
            "appiumLogs": True,
            "deviceLogs": True,
            "autoAcceptAlerts": True,
        },
    )
    return options


def build_driver(settings: Settings, session_name: str = "OnlineDuken session") -> webdriver.Remote:
    if settings.is_android and settings.is_browserstack:
        options: AppiumOptions = _android_browserstack_options(settings, session_name)
        driver = webdriver.Remote(
            command_executor=settings.browserstack_hub_url,
            options=options,
            client_config=_browserstack_client_config(settings),
        )
    elif settings.is_android:
        options = _android_local_options(settings)
        driver = webdriver.Remote(command_executor=settings.appium_server_url, options=options)
    elif settings.is_ios and settings.is_browserstack:
        options = _ios_browserstack_options(settings, session_name)
        driver = webdriver.Remote(
            command_executor=settings.browserstack_hub_url,
            options=options,
            client_config=_browserstack_client_config(settings),
        )
    else:
        options = _ios_local_options(settings)
        driver = webdriver.Remote(command_executor=settings.appium_server_url, options=options)

    driver.implicitly_wait(settings.implicit_wait_sec)
    return driver
