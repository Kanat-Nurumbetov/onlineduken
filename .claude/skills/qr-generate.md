---
description: Сгенерировать QR-картинки (common/megapolis) под заданный BIN/сумму и положить в artifacts/.
---

# Skill: qr-generate

Скил для генерации тестовых QR-изображений через `mobile_automation/qr_assets.py`. Используется для:
- предварительной готовки QR до запуска smoke (`pytest -m payments`)
- ручной проверки template'ов (`QR_COMMON_TEMPLATE`, `QR_MEGAPOLIS_TEMPLATE`)
- генерации QR с уникальным `invoice_id`/`contract` (чтобы не нарваться на дубль-платёж)

## Когда использовать
- Пользователь говорит "сгенерь QR", "сделай QR на 1000 тенге", "перевыпусти common QR"
- Перед прогоном QR-payment-смоука вручную
- Когда тест упал на QR и нужно проверить, валидный ли payload в картинке

## Что нужно от пользователя
- `CLIENT_BIN` (12 цифр) — обязательно, иначе `build_generated_qr_cases` вернёт `[]`
- `amount`, `invoice_id`, `invoice_title`, `megapolis_contract` — опционально, есть дефолты из `Settings`
- Какие типы QR нужны (`common`, `megapolis`, или оба)

## Шаги

1. Проверь, что есть `.env.local` с `CLIENT_BIN` (если нет в env). Если нет — попроси у пользователя BIN.
2. Если пользователь дал custom-значения — установи их в env перед вызовом:
   ```bash
   export CLIENT_BIN=123456789012
   export QR_AMOUNT=1000
   export QR_INVOICE_ID=10001
   ```
3. Запусти Python one-liner:
   ```bash
   python -c "
   from mobile_automation.config import Settings
   from mobile_automation.qr_assets import build_generated_qr_cases
   cases = build_generated_qr_cases(Settings())
   for c in cases:
       print(f'{c.name}: {c.image_path}')
       print(f'  payload: {c.payload}')
   "
   ```
4. Покажи пользователю:
   - Пути к сгенерированным PNG (обычно `artifacts/runtime/generated_qr_common_*.png`)
   - Payload каждого QR — для ручной проверки template'а
   - Размер файла (sanity check, не пустой ли)
5. Если нужно один QR (а не оба) — пользователь может отключить через `QR_COMMON_ENABLED=false` или `QR_MEGAPOLIS_ENABLED=false`.
6. Если нужен совсем простой QR из произвольного URL/строки (без template'а) — используй `ensure_qr_image`:
   ```bash
   python -c "
   from mobile_automation.config import Settings
   from mobile_automation.qr_assets import ensure_qr_image
   import os
   os.environ['QR_SOURCE_URL'] = 'https://example.com/your/payload'
   print(ensure_qr_image(Settings()))
   "
   ```

## Что НЕ делать
- Не коммитить сгенерированные PNG в репо — `artifacts/` в `.gitignore` намеренно
- Не использовать боевые BIN клиентов — только тестовые
- Не подменять template'ы без обновления `.env.example` — это сломает чужие прогоны
- Не вызывать `_build_qr_png` напрямую из тестов — используй `build_generated_qr_cases`

## Связанные модули
- `mobile_automation/qr_assets.py` — генерация
- `mobile_automation/qr_flow.py:push_qr_image_to_device` — заливка PNG на устройство (Local через adb, BrowserStack через `driver.push_file`)
- `mobile_automation/config.py:GeneratedQrCase` — структура (name/image_path/payload)

## Полезные команды
```bash
# Посмотреть существующие сгенерированные QR:
ls -lt artifacts/runtime/generated_qr_*.png 2>/dev/null | head

# Проверить payload QR-картинки (требует zbar/pyzbar):
# pip install pyzbar pillow
python -c "from pyzbar.pyzbar import decode; from PIL import Image; print(decode(Image.open('artifacts/runtime/generated_qr_common_XXX.png')))"

# Очистить старые QR:
rm artifacts/runtime/generated_qr_*.png
```
