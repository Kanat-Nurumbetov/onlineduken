.PHONY: build android ios parallel servers clean setup-ci

# Переменные
DOCKER_COMPOSE = docker-compose
PYTEST_WORKERS ?= 2

# Сборка образа
build:
	@echo "Building universal mobile testing image..."
	$(DOCKER_COMPOSE) build mobile-tests-android

# Только Android тесты
android:
	@echo "Running Android tests..."
	$(DOCKER_COMPOSE) up --build mobile-tests-android --abort-on-container-exit

# Только iOS тесты (требует macOS)
ios:
	@echo "Running iOS tests..."
	$(DOCKER_COMPOSE) --profile ios up --build mobile-tests-ios --abort-on-container-exit

# Параллельное выполнение на обеих платформах
parallel:
	@echo "Running tests on both platforms in parallel..."
	$(DOCKER_COMPOSE) --profile parallel up --build mobile-tests-parallel --abort-on-container-exit

# Только Appium серверы (без автоматического запуска тестов)
servers:
	@echo "Starting Appium servers..."
	$(DOCKER_COMPOSE) up --build appium-servers

# Локальные тесты
local-android:
	@echo "Running Android tests locally..."
	TEST_PLATFORM=android ANDROID_HEADLESS=1 APPIUM_EXTERNAL=1 ANDROID_APPIUM_HOST=127.0.0.1 ANDROID_APPIUM_PORT=4723 \
		pytest -q tests/test_payment.py

local-android-gui:
	@echo "Running Android tests locally (GUI emulator)..."
	TEST_PLATFORM=android ANDROID_HEADLESS=0 APPIUM_EXTERNAL=1 ANDROID_APPIUM_HOST=127.0.0.1 ANDROID_APPIUM_PORT=4723 \
		pytest -q tests/test_payment.py

local-ios:
	@echo "Running iOS tests locally (requires macOS)..."
	PLATFORM=ios ENABLE_ANDROID=false ENABLE_IOS=true ./scripts/universal_setup.sh

local-parallel:
	@echo "Running parallel tests locally..."
	PLATFORM=both PARALLEL_MODE=true ENABLE_ANDROID=true ENABLE_IOS=true PYTEST_WORKERS=$(PYTEST_WORKERS) ./scripts/universal_setup.sh

# Тесты с маркерами
test-smoke:
	@echo "Running smoke tests..."
	$(DOCKER_COMPOSE) run --rm mobile-tests-android python -m pytest tests/ -m smoke -v

test-regression:
	@echo "Running regression tests..."  
	$(DOCKER_COMPOSE) --profile parallel run --rm mobile-tests-parallel python -m pytest tests/ -m regression --dist=loadgroup -n $(PYTEST_WORKERS) -v

# Интерактивные команды
shell:
	$(DOCKER_COMPOSE) run --rm mobile-tests-android /bin/bash

shell-android:
	$(DOCKER_COMPOSE) exec mobile-tests-android /bin/bash

shell-ios:
	$(DOCKER_COMPOSE) --profile ios exec mobile-tests-ios /bin/bash

# Проверка статуса серверов
status:
	@echo "Checking Appium servers status..."
	@curl -s http://localhost:4723/status | jq -r '.value.build.version // "Android Appium not available"' | sed 's/^/Android Appium: /'
	@curl -s http://localhost:4724/status | jq -r '.value.build.version // "iOS Appium not available"' | sed 's/^/iOS Appium: /' 2>/dev/null || echo "iOS Appium: not available"

# Логи
logs:
	$(DOCKER_COMPOSE) logs -f

logs-android:
	$(DOCKER_COMPOSE) logs -f mobile-tests-android

logs-ios:
	$(DOCKER_COMPOSE) --profile ios logs -f mobile-tests-ios

logs-parallel:
	$(DOCKER_COMPOSE) --profile parallel logs -f mobile-tests-parallel

# Очистка
clean:
	@echo "Cleaning up..."
	$(DOCKER_COMPOSE) --profile ios --profile parallel down -v
	docker system prune -f
	rm -rf reports/* screenshots/*

# Настройка для CI/CD
setup-ci:
	@echo "Setting up CI/CD environment..."
	mkdir -p reports/{android,ios,parallel} screenshots/{android,ios}
	chmod +x scripts/*.sh

# Остановка всех контейнеров
stop:
	$(DOCKER_COMPOSE) --profile ios --profile parallel down

# Перезапуск сервисов
restart: stop
	$(DOCKER_COMPOSE) up -d appium-servers

# Отчеты
reports:
	@echo "Generating Allure reports..."
	allure generate reports/allure-results -o reports/allure-report --clean
	allure open reports/allure-report

# Проверка окружения
check:
	@echo "Checking environment and dependencies..."
	@docker --version
	@docker-compose --version
	@python3 --version
	@echo "Docker images:"
	@docker images | grep mobile-tests || echo "No mobile-tests images found"
