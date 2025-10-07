.PHONY: help
help:
	@echo "Доступные команды:"
	@echo "  make docker-up          - Запустить все сервисы (Appium + Emulator)"
	@echo "  make docker-down        - Остановить все сервисы"
	@echo "  make test-smoke         - Запустить smoke-тесты"
	@echo "  make test-all           - Запустить все тесты"
	@echo "  make test-smoke-local   - Smoke-тесты локально (без Docker)"
	@echo "  make ci-test            - Запуск для CI/CD"
	@echo "  make allure-report      - Сгенерировать Allure отчёт"
	@echo "  make clean              - Очистить артефакты"

# ============ Docker команды ============
.PHONY: docker-up
docker-up:
	@echo "🚀 Запуск Docker окружения..."
	docker-compose up -d appium android-emulator
	@echo "⏳ Ожидание готовности сервисов..."
	docker-compose exec -T android-emulator timeout 120 sh -c 'until adb shell getprop sys.boot_completed | grep 1; do sleep 5; done'
	@echo "✅ Окружение готово"

.PHONY: docker-down
docker-down:
	@echo "🛑 Остановка Docker окружения..."
	docker-compose down -v
	@echo "✅ Остановлено"

.PHONY: docker-logs
docker-logs:
	docker-compose logs -f

# ============ Тестовые команды (Docker) ============
.PHONY: test-smoke
test-smoke: docker-up
	@echo "🧪 Запуск smoke-тестов в Docker..."
	docker-compose run --rm tests pytest tests/test_smoke.py -v -s --tb=short --alluredir=allure-results
	@$(MAKE) docker-down

.PHONY: test-all
test-all: docker-up
	@echo "🧪 Запуск всех тестов в Docker..."
	docker-compose run --rm tests pytest tests/ -v -s --tb=short --alluredir=allure-results
	@$(MAKE) docker-down

.PHONY: test-payment
test-payment: docker-up
	@echo "🧪 Запуск payment тестов в Docker..."
	docker-compose run --rm tests pytest tests/test_payment.py -v -s --tb=short --alluredir=allure-results
	@$(MAKE) docker-down

# ============ CI/CD команда ============
.PHONY: ci-test
ci-test:
	@echo "🤖 CI/CD: Запуск тестов..."
	docker-compose up -d appium android-emulator
	@echo "⏳ Ожидание готовности..."
	sleep 60
	docker-compose run --rm tests pytest tests/test_smoke.py -v --tb=short --alluredir=allure-results --junit-xml=junit.xml || true
	docker-compose down -v
	@echo "✅ CI/CD тесты завершены"

# ============ Локальные команды (без Docker) ============
.PHONY: check-local-env
check-local-env:
	@command -v appium >/dev/null 2>&1 || { echo "❌ Appium не установлен"; exit 1; }
	@command -v adb >/dev/null 2>&1 || { echo "❌ ADB не установлен"; exit 1; }
	@pgrep -f appium >/dev/null || { echo "⚠️ Appium не запущен. Запустите: appium"; exit 1; }
	@adb devices | grep -q "device$$" || { echo "⚠️ Устройство/эмулятор не подключен"; exit 1; }
	@echo "✅ Локальное окружение готово"

.PHONY: test-smoke-local
test-smoke-local: check-local-env
	@echo "🧪 Запуск smoke-тестов локально..."
	pytest tests/test_smoke.py -v -s --tb=short --alluredir=allure-results

.PHONY: test-all-local
test-all-local: check-local-env
	@echo "🧪 Запуск всех тестов локально..."
	pytest tests/ -v -s --tb=short --alluredir=allure-results

# ============ Отчёты ============
.PHONY: allure-report
allure-report:
	@echo "📊 Генерация Allure отчёта..."
	@command -v allure >/dev/null 2>&1 || { echo "❌ Allure не установлен"; exit 1; }
	allure serve allure-results

.PHONY: allure-generate
allure-generate:
	@echo "📊 Генерация статического Allure отчёта..."
	allure generate allure-results -o allure-report --clean
	@echo "✅ Отчёт создан в: allure-report/index.html"

# ============ Очистка ============
.PHONY: clean
clean:
	@echo "🧹 Очистка артефактов..."
	rm -rf allure-results allure-report .pytest_cache __pycache__ junit.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Очистка завершена"

.PHONY: clean-docker
clean-docker: docker-down
	@echo "🧹 Полная очистка Docker..."
	docker system prune -af --volumes
	@echo "✅ Docker очищен"