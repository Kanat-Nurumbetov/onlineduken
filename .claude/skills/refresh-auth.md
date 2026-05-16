---
description: Обновить B2B auth URL/токен через `mobile_automation.runtime_auth`, проверить валидность, прокинуть в `.env.local`.
---

# Skill: refresh-auth

Скилл для получения свежего B2B auth URL без перезапуска smoke. OnlineDuken WebView подгружается по deeplink с одноразовым `ob-auth-token`, токен живёт ~30 минут (см. `B2B_AUTH_CACHE_TTL_SEC`).

## Когда использовать
- Тесты падают на webview-входе с "auth expired"
- Перед длинным debug-сеансом, когда хочется свежий токен
- Пользователь говорит "обнови токен", "перевыпусти auth", "получи новый URL"

## Шаги

1. Проверь, есть ли `.env.local` с переменными резолва. Минимум один источник из:
   - `B2B_INTERNAL_LOGIN_URL` + `B2B_INTERNAL_CLIENT_ID` + `B2B_INTERNAL_CLIENT_SECRET`
   - `B2B_AUTH_FETCH_COMMAND` — кастомная shell-команда, возвращающая URL/token
   - `B2B_APP_AUTH_BOOTSTRAP=true` — обход через реальный логин (требует Appium + устройство)

2. Запусти Python-сниппет:
   ```bash
   python -c "from mobile_automation.config import Settings; from mobile_automation.runtime_auth import resolve_shared_b2b_auth_url; url = resolve_shared_b2b_auth_url(Settings()); print(url or 'NO_URL_RESOLVED')"
   ```

3. Если URL вернулся:
   - Проверь его через `is_valid_b2b_auth_url`
   - Покажи пользователю первые ~80 символов URL и предложи записать в `.env.local` как `B2B_AUTH_URL=<url>`
   - Не сохраняй автоматически без подтверждения — это запись в окружение

4. Если URL пустой:
   - Проверь `artifacts/runtime/b2b_auth.json` — есть ли валидный кеш
   - Проверь все 3 стратегии резолва по очереди: какая упала и почему
   - Покажи последний `WARNING` лог из `runtime_auth`

5. Если был использован app-login bootstrap — покажи где артефакты (`artifacts/app_auth_bootstrap_*`)

## Что НЕ делать
- Не коммитить полученный URL — он одноразовый и содержит токен
- Не вызывать `app_auth_bootstrap` без подтверждения — он реально запускает драйвер и логинится через UI
- Не очищать кеш руками без причины (это сбросит работающий токен)

## Полезные команды
```bash
# Проверить кеш:
cat artifacts/runtime/b2b_auth.json

# Очистить кеш (форсировать новый резолв):
rm artifacts/runtime/b2b_auth.json

# Проверить валидность URL:
python -c "from mobile_automation.config import is_valid_b2b_auth_url; print(is_valid_b2b_auth_url('<URL>'))"
```
