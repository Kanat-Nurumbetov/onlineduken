
#!/bin/bash

set -e

# Функция логирования
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$PLATFORM] $*"
}

# Функция очистки
cleanup() {
    log "Cleaning up..."
    if [ "$ENABLE_ANDROID" = "true" ]; then
        pkill -f "qemu-system" || true
        adb kill-server || true
    fi
    if [ "$ENABLE_IOS" = "true" ]; then
        xcrun simctl shutdown all || true
    fi
    pkill -f "appium" || true
}

trap cleanup EXIT

# Переменные окружения с значениями по умолчанию
PLATFORM=${PLATFORM:-"android"}
ENABLE_ANDROID=${ENABLE_ANDROID:-"true"}
ENABLE_IOS=${ENABLE_IOS:-"false"}
APPIUM_HOST=${APPIUM_HOST:-"0.0.0.0"}
APPIUM_PORT=${APPIUM_PORT:-"4723"}
PARALLEL_MODE=${PARALLEL_MODE:-"false"}

# Android настройки
ANDROID_AVD_NAME=${ANDROID_AVD_NAME:-"test_emulator"}
ANDROID_API_LEVEL=${ANDROID_API_LEVEL:-"30"}
ANDROID_ARCH=${ANDROID_ARCH:-"x86_64"}
EMULATOR_WAIT_TIME=${ANDROID_EMULATOR_WAIT_TIME:-300}

# iOS настройки  
IOS_PLATFORM_VERSION=${IOS_PLATFORM_VERSION:-"15.0"}
IOS_DEVICE_NAME=${IOS_DEVICE_NAME:-"iPhone 13"}

log "Starting Universal Mobile Test Environment"
log "Platform: $PLATFORM, Android: $ENABLE_ANDROID, iOS: $ENABLE_IOS, Parallel: $PARALLEL_MODE"

# Функции для Android
setup_android() {
    if [ "$ENABLE_ANDROID" != "true" ]; then
        return 0
    fi
    
    log "Setting up Android environment..."
    
    # Создание AVD если не существует
    if ! avdmanager list avd | grep -q "$ANDROID_AVD_NAME"; then
        log "Creating Android AVD: $ANDROID_AVD_NAME"
        echo no | avdmanager create avd \
            --force \
            --name "$ANDROID_AVD_NAME" \
            --package "system-images;android-${ANDROID_API_LEVEL};google_apis;${ANDROID_ARCH}" \
            --abi "google_apis/${ANDROID_ARCH}"
    fi
    
    # Запуск эмулятора
    log "Starting Android emulator..."
    emulator -avd "$ANDROID_AVD_NAME" \
        -no-window \
        -no-audio \
        -no-snapshot \
        -gpu swiftshader_indirect \
        -camera-back none \
        -camera-front none \
        -memory 2048 \
        -partition-size 4096 \
        -port 5554 &
    
    # Ожидание загрузки
    adb wait-for-device
    
    timeout="$EMULATOR_WAIT_TIME"
    while [[ $timeout -gt 0 ]]; do
        if adb shell getprop sys.boot_completed | grep -q "1"; then
            log "Android emulator booted successfully"
            break
        fi
        sleep 5
        ((timeout -= 5))
    done
    
    if [[ $timeout -le 0 ]]; then
        log "ERROR: Android emulator failed to boot"
        return 1
    fi
    
    # Оптимизация для тестирования
    adb shell settings put global window_animation_scale 0.0
    adb shell settings put global transition_animation_scale 0.0  
    adb shell settings put global animator_duration_scale 0.0
    
    log "Android environment ready"
}

# Функции для iOS
setup_ios() {
    if [ "$ENABLE_IOS" != "true" ]; then
        return 0
    fi
    
    log "Setting up iOS environment..."
    
    # Проверяем платформу
    if [ "$(uname)" != "Darwin" ]; then
        log "WARNING: iOS setup on non-macOS system. Skipping simulator setup."
        return 0
    fi
    
    # Получаем UDID симулятора
    DEVICE_UDID=$(xcrun simctl list devices | grep "$IOS_DEVICE_NAME" | grep "$IOS_PLATFORM_VERSION" | awk -F'[()]' '{print $2}' | head -1)
    
    if [[ -z "$DEVICE_UDID" ]]; then
        log "Creating iOS Simulator: $IOS_DEVICE_NAME ($IOS_PLATFORM_VERSION)"
        DEVICE_TYPE=$(xcrun simctl list devicetypes | grep "$IOS_DEVICE_NAME" | head -1 | awk -F'[()]' '{print $(NF-1)}')
        RUNTIME=$(xcrun simctl list runtimes | grep "iOS $IOS_PLATFORM_VERSION" | head -1 | awk -F'[()]' '{print $(NF-1)}')
        DEVICE_UDID=$(xcrun simctl create "Test-${IOS_DEVICE_NAME//[^a-zA-Z0-9]/-}-$IOS_PLATFORM_VERSION" "$DEVICE_TYPE" "$RUNTIME")
    fi
    
    # Запуск симулятора
    log "Starting iOS Simulator with UDID: $DEVICE_UDID"
    xcrun simctl boot "$DEVICE_UDID" || true
    
    export IOS_DEVICE_UDID="$DEVICE_UDID"
    log "iOS environment ready"
}

# Запуск Appium сервера
start_appium() {
    local port=${1:-$APPIUM_PORT}
    local platform_suffix=${2:-""}
    
    log "Starting Appium server$platform_suffix on $APPIUM_HOST:$port"
    
    # Настройки безопасности и драйверы
    local appium_args=(
        "server"
        "--address" "$APPIUM_HOST"
        "--port" "$port"
        "--relaxed-security"
        "--log-timestamp"
        "--log-level" "info"
    )
    
    # Добавляем специфичные для платформы настройки
    if [ "$ENABLE_ANDROID" = "true" ]; then
        appium_args+=("--allow-insecure" "chromedriver_autodownload")
    fi
    
    appium "${appium_args[@]}" &
    local appium_pid=$!
    
    # Ожидание запуска Appium
    timeout=60
    while [[ $timeout -gt 0 ]]; do
        if curl -sSf "http://$APPIUM_HOST:$port/status" >/dev/null 2>&1; then
            log "Appium server$platform_suffix started successfully (PID: $appium_pid)"
            return 0
        fi
        sleep 2
        ((timeout -= 2))
    done
    
    log "ERROR: Appium server$platform_suffix failed to start"
    return 1
}

# Запуск тестов
run_tests() {
    if [ "$RUN_TESTS" = "true" ]; then
        log "Running tests..."
        
        # Создание директорий для отчетов
        mkdir -p reports screenshots
        
        # Определяем параметры pytest в зависимости от режима
        local pytest_args=(
            "tests/"
            "--alluredir=reports/allure-results"
            "--tb=short"
            "--capture=no"
            "-v"
        )
        
        if [ "$PARALLEL_MODE" = "true" ]; then
            pytest_args+=("--dist=loadgroup" "-n" "${PYTEST_WORKERS:-2}")
        fi
        
        if [ "$PLATFORM" != "both" ]; then
            pytest_args+=("--platform=$PLATFORM")
        fi
        
        python -m pytest "${pytest_args[@]}"
        
        log "Test execution completed"
    else
        log "Test execution skipped (RUN_TESTS=false). Keeping services alive..."
        wait
    fi
}

# Основная логика
main() {
    log "Initializing universal test environment..."
    
    # Определяем что нужно запускать
    case "$PLATFORM" in
        "android")
            ENABLE_ANDROID=true
            ENABLE_IOS=false
            ;;
        "ios") 
            ENABLE_ANDROID=false
            ENABLE_IOS=true
            ;;
        "both"|"parallel")
            ENABLE_ANDROID=true
            ENABLE_IOS=true
            PARALLEL_MODE=true
            ;;
    esac
    
    # Запуск Android ADB если нужен
    if [ "$ENABLE_ANDROID" = "true" ]; then
        adb start-server
    fi
    
    # Настройка платформ
    if [ "$ENABLE_ANDROID" = "true" ]; then
        setup_android || exit 1
    fi
    
    if [ "$ENABLE_IOS" = "true" ]; then
        setup_ios || exit 1
    fi
    
    # Запуск Appium серверов
    if [ "$PARALLEL_MODE" = "true" ]; then
        # Параллельный режим - два сервера на разных портах
        if [ "$ENABLE_ANDROID" = "true" ]; then
            start_appium 4723 " (Android)" || exit 1
        fi
        if [ "$ENABLE_IOS" = "true" ]; then
            start_appium 4724 " (iOS)" || exit 1  
        fi
    else
        # Один сервер для выбранной платформы
        start_appium "$APPIUM_PORT" || exit 1
    fi
    
    # Запуск тестов или ожидание
    run_tests
}

# Если скрипт запущен напрямую
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
