---
description: Запустить smoke-набор тестов (локально или BrowserStack) с правильными флагами, собрать Allure, показать сводку падений.
---

# Skill: run-smoke

Скилл для запуска smoke-набора OnlineDuken автотестов. Поддерживает два режима:
- **local** — Appium локально с эмулятором/устройством (требуется `.env.local` с PHONE_NUMBER, SMS_CODE, PIN_CODE, путями SDK)
- **browserstack** — App Automate (требуется `.env.local` с BROWSERSTACK_USERNAME, BROWSERSTACK_ACCESS_KEY, BROWSERSTACK_APP_ANDROID)

## Когда использовать
- Пользователь говорит "запусти smoke", "прогон smoke", "погоняй тесты", "проверь BrowserStack"
- После рефакторинга мобильного flow — для регрессии
- Перед коммитом нетривиальных изменений в `flows.py`, `qr_flow.py`, `runtime_auth.py`

## Шаги

1. Уточни у пользователя режим (`local` или `browserstack`) если не указан и не очевиден из контекста.
2. Уточни какие маркеры запускать (по умолчанию для BrowserStack: `"smoke and browserstack_safe and not manual"`, для local: `"smoke and not manual"`).
3. Прочитай `.env.local` (если есть) чтобы понять что сконфигурировано. Если ключевых переменных нет — предложи пользователю заполнить.
4. Проверь готовность среды:
   - Для local: проверь что устройство видно (`adb devices`) и Appium стартует (`pytest` сам запустит как fixture). Запусти `python -m mobile_automation.healthcheck` чтобы проверить test-env.
   - Для browserstack: запусти `python -m mobile_automation.healthcheck` тем же образом.
5. Запусти команду pytest:
   ```bash
   pytest -m "<MARKERS>" --alluredir=allure-results -n <WORKERS>
   ```
   Где `<WORKERS>` = 1 для local (если нет `LOCAL_ANDROID_DEVICE_MATRIX`), иначе 3.
6. Если ставится падение — НЕ пытайся "пофиксить flaky" перезапуском. Покажи сводку:
   - Какие тесты упали, на каком шаге Allure step
   - Какие артефакты появились в `artifacts/` (имена .png, .xml, .txt)
   - Если есть в стектрейсе характерное — `TimeoutException`, `WebDriverException`, `AssertionError` — назови причину одной строкой
7. Предложи дальше: либо запустить `triage-failure` (по последнему упавшему), либо `refresh-auth` (если падает на auth-шагах), либо посмотреть конкретный артефакт.

## Что НЕ делать
- Не запускать smoke если `.env.local` отсутствует — сначала спросить
- Не запускать с `--rerun-failed` или подобными ретраями, скрывающими flaky behavior
- Не передавать `-n auto` для local target без `LOCAL_ANDROID_DEVICE_MATRIX` — это сорвётся
- Не править тестовый код после первого падения "наугад" — сначала прочитать артефакты

## Полезные команды
```bash
# Локальный smoke на одном эмуляторе:
pytest -m "smoke and not manual" --alluredir=allure-results

# BrowserStack без WebView:
pytest -m "smoke and browserstack_safe and not manual" -n 3 --maxfail=1 --alluredir=allure-results

# Только QR-payments:
pytest -m "smoke and payments" --alluredir=allure-results

# Healthcheck:
python -m mobile_automation.healthcheck
```
