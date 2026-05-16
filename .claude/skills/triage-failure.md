---
description: Разобрать последний упавший тест — артефакты в artifacts/, Allure-результаты, page source, гипотеза о причине.
---

# Skill: triage-failure

Скил для системного разбора падений smoke/web. Цель — НЕ "перезапустить и надеяться", а понять причину: timeout vs locator drift vs изменение окружения (auth, store-popup, package version).

## Когда использовать
- После провала `pytest -m smoke` локально или в CI
- Когда пользователь говорит "почему упало?", "разбери последний crash", "что случилось с QR-тестом"
- Перед коммитом фикса локатора/таймаута — убедиться что лечится корень, а не симптом

## Что есть в распоряжении
1. **`artifacts/`** — `capture_native_debug_state(driver, prefix)` и `capture_web_debug_state(driver, prefix)` пишут сюда тройки:
   - `<prefix>.png` — скриншот
   - `<prefix>.xml` (native) или `<prefix>.html` (web) — page source
   - `<prefix>.txt` — метаданные (current_activity, current_package, contexts, current_url, current_context)
2. **`allure-results/`** — JSON-результаты с `statusDetails.trace` если запуск был с `--alluredir`
3. **Allure-аттачи на failure** — `attach_driver_state` в [conftest.py](tests/conftest.py) автоматически вешает screenshot + page_source + JSON-метаданные при падении (если allure-pytest установлен)

## Шаги

1. Найди свежие артефакты:
   ```bash
   ls -lt artifacts/*.txt 2>/dev/null | head -10
   ls -lt allure-results/*-result.json 2>/dev/null | head -5
   ```
2. Прочитай `.txt` сначала — это самые компактные метаданные. Что искать:
   - `current_activity` — где app остановился. `AuthActivity` = логин не прошёл. `B2BActivity` = native контейнер OK, но WebView мог не открыться. `QrActivity` = застряли на QR.
   - `current_package` — если не `kz.halyk.onlinebank.stage`, приложение свернулось/убилось
   - `contexts` — есть ли WEBVIEW_* контекст. Если только `NATIVE_APP` — WebView не поднялся.
   - `current_url` (для web) — открыт ли `/web/customer-frontend/`
3. Если есть Allure JSON — прочитай `statusDetails.trace` и `statusDetails.message`. Там тип исключения и место.
4. Открой `.png` и `.xml/.html` если нужно подтвердить визуально. Для XML — поищи маркеры:
   - `pinEditText` — застряли на pin
   - `phone_input` — застряли на phone
   - `bottom-overlay_visible` (в html) — застрял store-popup
5. Соотнеси prefix с кодом — найди где он вызывается:
   ```bash
   grep -rn "capture_native_debug_state.*<PREFIX>" mobile_automation/
   grep -rn "capture_web_debug_state.*<PREFIX>" mobile_automation/
   ```
   Это покажет точное место в [flows.py](mobile_automation/flows.py) или [qr_flow.py](mobile_automation/qr_flow.py).
6. Сформулируй гипотезу одной фразой:
   - **Auth drift**: `current_activity=AuthActivity` + `phone_input` в page_source → SMS/PIN не подтвердился, проверь `B2B_AUTH_URL` cache TTL → запусти `refresh-auth`
   - **Store popup**: `bottom-overlay_visible` в html → `choose_first_store_in_webview_if_present` не сработал, проверь маркеры в `KNOWN_STORE_MARKERS`
   - **Locator drift**: элемент по `By.ID/By.XPATH` не найден → page_source показывает другую структуру → требуется обновление [pages/native.py](mobile_automation/pages/native.py) или [pages/web.py](mobile_automation/pages/web.py)
   - **WebView не поднялся**: только `NATIVE_APP` в contexts на BrowserStack → проверь что `BROWSERSTACK_WEBVIEW_ENABLED=true` и сборка с debuggable WebView
   - **Timeout**: всё в page_source выглядит правильно, но `TimeoutException` → реальная медлительность среды, НЕ увеличивай таймаут вслепую — добавь условное ожидание через `wait_until` из `mobile_automation/wait_utils.py`
7. Покажи пользователю:
   - Имя упавшего теста
   - Хайлайт `.txt` (3-5 строк)
   - Гипотеза одной строкой
   - Какой файл смотреть для фикса
   - Предложи следующий скил: `refresh-auth` / `run-smoke` (после фикса) / прочитать конкретный артефакт

## Что НЕ делать
- **Не перезапускать тест "ещё раз посмотреть"** — артефакт уже есть. Перезапуск = потеря времени.
- **Не увеличивать `timeout=` "пока не пройдёт"** — это маскировка. Если 30s не хватает, скорее всего, нет нужного условия ожидания.
- **Не править локатор на основе одного падения** — проверь, не было ли в прошлый прогон другого. UI мог быть в разных состояниях.
- **Не удалять артефакты до разбора** — `.gitignore` не даст их закоммитить, но локально они нужны
- **Не "лечить" через `pytest --rerun-failed`** — это скрывает flakiness, а не решает

## Полезные команды
```bash
# Свежие артефакты:
ls -lt artifacts/*.txt | head

# Что упало в последнем Allure-прогоне:
python -c "
import json, glob
from pathlib import Path
for path in sorted(glob.glob('allure-results/*-result.json'), key=lambda p: Path(p).stat().st_mtime, reverse=True)[:5]:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('status') == 'failed':
        print(data.get('name'), '->', data.get('statusDetails', {}).get('message', '')[:200])
"

# Найти все XML с конкретным маркером:
grep -l "pinEditText" artifacts/*.xml

# Найти где prefix регистрируется:
grep -rn "capture_.*_debug_state" mobile_automation/ tests/
```
