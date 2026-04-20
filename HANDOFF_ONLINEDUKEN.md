# OnlineDuken Handoff

## Purpose

This file is the main handoff for continuing the work on another device, in a browser, or through GitHub.

Goal of the project:
- analyze the `Halyk Bank` stage APK;
- reach `OnlineDuken`;
- identify native and WebView parts;
- collect locators and routes for future E2E automation;
- define a first smoke suite for the most important business flows, with payments as top priority.

## Files Received From User

- APK: `C:\Users\Kanat\Downloads\halyk_bank_app.apk`
- Test phone: `7772229999`
- PIN for app login: `0000`
- SMS rule: any numeric code can be entered on the SMS confirmation screen

## Key Findings

### Main app

- APK is valid and readable.
- Package name: `kz.halyk.onlinebank.stage`
- Version from `aapt`: `1.0.1431`
- Launch activity: `kz.halyk.onlinebank.ui_release4.screens.splash.SplashActivity`

### Login flow

Native screens and stable ids were found for:
- login screen;
- SMS confirmation screen;
- passcode creation;
- passcode unlock;
- permission and onboarding-related app screens.

Important native ids:
- `kz.halyk.onlinebank.stage:id/phone_input`
- `kz.halyk.onlinebank.stage:id/login_button`
- `kz.halyk.onlinebank.stage:id/lang_text_view`
- `kz.halyk.onlinebank.stage:id/become_client_button`
- `kz.halyk.onlinebank.stage:id/sms_subtitle`
- `kz.halyk.onlinebank.stage:id/sms_remaining`
- `kz.halyk.onlinebank.stage:id/et`
- `kz.halyk.onlinebank.stage:id/pinEditText`
- `kz.halyk.onlinebank.stage:id/text_forgot_pin`
- `kz.halyk.onlinebank.stage:id/webview`

### Stage outage that happened earlier

At one point the stage backend returned `503` for:
- `https://testapi.onlinebank.kz/authentication/get-sms/7772229999?app=android`

This was later resolved and login became possible again.

### OnlineDuken architecture

- `OnlineDuken` is reached through the main application.
- It is loaded inside `B2BActivity`.
- `B2BActivity` is a native shell containing a `WebView`.
- Current native container:
  - activity: `kz.halyk.onlinebank.ui_release4.screens.b2b.activity.B2BActivity`
  - WebView id: `kz.halyk.onlinebank.stage:id/webview`

### Important note about the separate B2B package

There is a separate installed package in the emulator:
- `com.example.b2b`

But it is not the real business target. It opens a placeholder app with:
- `Hello Android!`

So this package should not be the main focus for E2E.

### How OnlineDuken was reached reliably

Direct opening of `B2BActivity` from shell failed because it is not exported.

Reliable route discovered:
1. open deep link:
   - `https://halyk.onlinebank.kz/appLink/b2b/`
2. app asks for passcode unlock;
3. enter PIN `0000`;
4. app opens `B2BActivity`;
5. `OnlineDuken` home appears inside WebView.

This is currently the most stable technical entry point found for automation.

## OnlineDuken Web Routes Found

Base URL:
- `https://b2b.test.onlinebank.kz/web/customer-frontend/`

Main routes discovered:
- Home: `/web/customer-frontend/`
- Catalog: `/web/customer-frontend/distributors`
- Orders: `/web/customer-frontend/orders`
- Bonuses: `/web/customer-frontend/bonuses`
- Payment to supplier: `/web/customer-frontend/distributors/qr-distributors`
- Cart: `/web/customer-frontend/cart`
- More: `/web/customer-frontend/more`

## WebView / DOM Signals Found

### Bottom navigation

Stable anchors found:
- `a[href="/web/customer-frontend/"]` for `Главная`
- `a[href="/web/customer-frontend/distributors"]` for `Каталог`
- `a[href="/web/customer-frontend/cart"]` for `Корзина`
- `a[href="/web/customer-frontend/more"]` for `Еще`

The `QR` tab currently also points to:
- `a[href="/web/customer-frontend/"]`

That likely means:
- either SPA logic is attached in JS;
- or QR is handled through a client-side click handler rather than unique URL alone.

### Home page

Observed content:
- store / address block with `QQQQQ`
- promo banner
- quick actions:
  - `Заказы`
  - `Бонусы`
  - `Оплата`
- supplier/product content
- supplier payment section

Useful selectors seen in DOM:
- `button.banner-btn`
- `a[href="/web/customer-frontend/orders"]`
- `a[href="/web/customer-frontend/bonuses"]`
- `a[href="/web/customer-frontend/distributors/qr-distributors"]`
- product add button with text `В корзину`

### Catalog page

Observed content:
- title `Выберите поставщика`
- supplier cards
- `Создать заказ`
- some suppliers also show connect / view catalog actions

Useful selectors seen in DOM:
- `h1.distributors__header-title`
- `div.distributor-card`
- `button` with text `Создать заказ`

### Orders page

Observed content:
- title `Мои заказы`

### Bonuses page

Observed content:
- title `Бонусы`
- bonus metrics including `0.4 %` and `70 %`
- a history-related link was found in DOM summary

Useful anchors:
- link with text `ссылка`
- relative target noted in DOM data:
  - `bonuses/changes-history`

### Payment page

Observed content:
- title `Произвести оплату поставщику`
- tabs:
  - `Все`
  - `Ручная оплата`
  - `QR оплата`

Useful selectors:
- `button.tabs-btn`
- text-based tab selection

### Cart page

Observed content:
- title `Корзина`
- `Создать заказ`

### More page

Observed content:
- title `Еще`
- menu items:
  - `Связаться с нами`
  - `Часто задаваемые вопросы`
  - `Кассиры Online Duken`
  - `Оферта`
  - `Выйти из OnlineDuken`

Useful DOM classes:
- `more-item-container-title`
- `exit-item`

## Recommended Automation Strategy

### Tech direction

Recommended stack:
- `Appium`
- Android native context for main app shell
- WebView context switching for `OnlineDuken`
- `Page Object Model`

Why:
- main app login is native;
- `OnlineDuken` content is web-based in `WebView`;
- we already confirmed WebView remote debugging was available and DOM could be inspected.

### Initial POM split

Suggested first page objects:
- `LoginPage`
- `SmsCodePage`
- `CreatePasscodePage`
- `UnlockPasscodePage`
- `MainAppOnboardingPage`
- `B2BWebViewContainerPage`
- `OnlineDukenHomePage`
- `CatalogPage`
- `OrdersPage`
- `BonusesPage`
- `PaymentPage`
- `CartPage`
- `MorePage`

## Important Constraints / Risks

- Contract selection ending with `376` was requested by the user, but this exact step was not fully validated end-to-end in the UI because `OnlineDuken` was reached through the `b2b` deeplink route and passcode unlock.
- Some internal onboarding screens in the main app behaved inconsistently under plain `adb tap`.
- Some deep SPA actions in WebView were not fully opened by simple DOM `.click()` scripts, which suggests Appium WebView context or a real browser automation style will be more reliable than ad hoc JS dispatch for final E2E tests.
- The `QR` tab appears to share the same route as `Главная`, so route-only assertions may be insufficient there.

## Smoke Suite Draft

Most important by business priority:
1. QR payment
2. Invoice payment from home
3. Cart and order creation
4. OnlineDuken login entry
5. Supplier visibility in catalog
6. Orders navigation
7. Bonuses and bonus history

See:
- `C:\Users\Kanat\Documents\New project\TEST_CASES_SMOKE_DRAFT.md`

## Where To Continue Next

Best next step:

## Update On 2026-04-20 (Cart Smoke Deferred)

- Cart/order smoke is intentionally paused until a stable supplier is prepared in the test environment.
- Temporary project rule:
  - `test_smoke_cart_and_order_creation` -> explicit `skip`
  - `test_smoke_cart_and_order_creation_from_home_optional` -> explicit `skip`
- Why this was done:
  - the cart flow itself is already partially researched
  - current supplier data is not deterministic enough for reliable smoke automation
  - one explored supplier reached categories and then an empty subcategory page, which makes the flow flaky by test data rather than by automation logic
- Current expectation for future re-enable:
  - user provides a stable supplier with predictable category/product availability
  - then cart smoke can be completed and unskipped without redesigning the suite
- review and approve smoke cases;
- then scaffold automation project and page objects;
- then implement the highest-priority flows first:
  - QR payment
  - invoice payment
  - cart + order creation

## Update On 2026-04-16

After the original analysis and handoff package, a local automation project scaffold was created in this same repository.

Added project pieces:
- Python project configuration
- `pytest` markers for `smoke` and `manual`
- local and BrowserStack driver factory
- environment healthcheck module
- native and WebView page objects
- initial smoke test skeleton
- manual test placeholder
- GitHub Actions workflows

Relevant project files added after the initial handoff:
- `C:\Users\Kanat\Documents\New project\README.md`
- `C:\Users\Kanat\Documents\New project\pyproject.toml`
- `C:\Users\Kanat\Documents\New project\pytest.ini`
- `C:\Users\Kanat\Documents\New project\.env.example`
- `C:\Users\Kanat\Documents\New project\mobile_automation\config.py`
- `C:\Users\Kanat\Documents\New project\mobile_automation\driver_factory.py`
- `C:\Users\Kanat\Documents\New project\mobile_automation\healthcheck.py`
- `C:\Users\Kanat\Documents\New project\mobile_automation\flows.py`
- `C:\Users\Kanat\Documents\New project\mobile_automation\pages\native.py`
- `C:\Users\Kanat\Documents\New project\mobile_automation\pages\web.py`
- `C:\Users\Kanat\Documents\New project\tests\smoke\test_smoke_suite.py`
- `C:\Users\Kanat\Documents\New project\tests\manual\test_manual_suite.py`
- `C:\Users\Kanat\Documents\New project\.github\workflows\smoke.yml`
- `C:\Users\Kanat\Documents\New project\.github\workflows\manual.yml`

Current direction after scaffold creation:
- `smoke` tests should run on push;
- before smoke CI execution, test environment availability must be checked;
- all non-smoke tests should run manually only;
- BrowserStack support is built into the config and CI shape;
- Android is the active first implementation target;
- iOS support is prepared at the project structure level but still needs real app data and flow validation.

New canonical status file:
- `C:\Users\Kanat\Documents\New project\PROJECT_PROGRESS.md`

Going forward:
- update `PROJECT_PROGRESS.md` after each meaningful project step;
- keep this handoff file for big-picture context;
- keep chronology/history and artifact files as historical reference.

### Additional Context Split Confirmed By User

User clarified which `OnlineDuken` screens are native and which are not.

Native screens inside `OnlineDuken`:
- QR flow
- gallery picker used for QR upload
- cashier page
- all nested screens inside cashier functionality

All other `OnlineDuken` screens should be treated as `WebView` unless future capture proves otherwise.

Automation implication:
- after entering `OnlineDuken`, the default working context should be `WEBVIEW_kz.halyk.onlinebank.stage`
- switch back to `NATIVE_APP` only for QR, gallery/system picker, and cashier-related flows

Additional validated facts from local probing:
- native home entry through the real `OnlineDuken` shortcut is more reliable than the earlier deeplink workaround
- the native home currently shows contract `name050201.705376`
- the first captured store in the `OnlineDuken` store-selection popup is:
  - `QQQQQ`
  - `0455b1fd-7001-4417-ac6c-f3897d98bce8`

## Update On 2026-04-16 (Local Safe Smoke Pass)

The non-payment local safe smoke subset is now green.

Passing subset:
- `OnlineDuken` entry
- catalog visibility
- orders navigation
- bonuses navigation
- bonus history visibility

Latest passing local result:
- `4 passed in 129.02s`

Important implementation notes:
- the safe subset currently excludes:
  - `QR`
  - invoice payment
  - cart/order creation
- the safe subset now runs with a shared Appium session for stability
- entry into `OnlineDuken` is now resilient to flaky native-home detection:
  - native shortcut is still the first attempt when available
  - deeplink remains as fallback
- the `OnlineDuken` store-selection popup is confirmed as `WebView`, not native
- the first store is auto-selected during entry

Confirmed current WebView route / locator facts:
- home route:
  - `/web/customer-frontend/`
- catalog route:
  - `/web/customer-frontend/distributor`
- bonuses route:
  - `/web/customer-frontend/bonuses`
- bonus history card locator shape:
  - `div.card.card-item[routerlink="./history"]`

Useful latest probe artifacts:
- `C:\Users\Kanat\Documents\New project\artifacts\webview_after_onlineduken_entry.html`
- `C:\Users\Kanat\Documents\New project\artifacts\webview_after_onlineduken_entry.png`
- `C:\Users\Kanat\Documents\New project\artifacts\bonuses_page_probe.html`
- `C:\Users\Kanat\Documents\New project\artifacts\bonuses_page_probe.png`
- `C:\Users\Kanat\Documents\New project\artifacts\catalog_page_probe.html`
- `C:\Users\Kanat\Documents\New project\artifacts\catalog_page_probe.png`

## Update On 2026-04-16 (Token-Based Auth Entry)

A token-based `OnlineDuken` entry mode was added to the automation project.

New env/config shape:
- `ONLINEDUKEN_ENTRY_MODE=token`
- `B2B_AUTH_URL=...`
- or `B2B_OB_AUTH_TOKEN=...`

Important technical result:
- Android does not resolve `https://b2b.test.onlinebank.kz/web/customer-frontend/auth?...` as a direct app link for `kz.halyk.onlinebank.stage`
- so the project does not rely on this URL as a pure Android deep link

Current implementation:
- try auth URL deep link first
- if that fails, open `OnlineDuken` container first
- once inside `WEBVIEW_kz.halyk.onlinebank.stage`, load the token auth URL in WebView

Verified local result:
- token-based entry smoke passed locally
- latest result:
  - `1 passed in 110.04s`

Meaning in practice:
- the token is useful for bypassing WebView-side auth
- it does not completely replace Android-side entry from a cold app start

## Update On 2026-04-16 (Token Safe Smoke Pass)

Token mode was improved further by normalizing auth URLs automatically.

Normalization applied:
- add `lang=ru` when missing
- add `navigateTo=home` when missing

Reason:
- a bare auth URL with only `ob-auth-token` was loading the auth shell/navbar but not a fully usable `OnlineDuken` home flow

After that change, the full local non-payment safe smoke subset also passed in token mode.

Latest token-mode passing result:
- `4 passed in 103.88s`

Meaning now:
- both entry styles are currently usable for the safe subset:
  - full app/mobile entry
  - token-based fast entry
- token mode is now the stronger base for faster local runs and future parallel smoke work

## Update On 2026-04-16 (Parallel Execution Position)

Parallel execution was clarified and partially prepared in the project.

Current rule:
- true parallel smoke is intended for `BrowserStack`
- local one-emulator execution stays sequential

Why local parallel is blocked:
- the current local bench uses one Android emulator and one Appium/device session
- running multiple pytest workers against the same emulator would produce session collisions, not meaningful parallelism

Project changes made:
- `pytest-xdist` added to dependencies
- local protection added so `pytest -n ...` with `TARGET=local` exits early with a clear message

Practical meaning:
- the suite is now parallel-ready at the pytest/project level
- real parallel execution should be used with isolated BrowserStack sessions later
- verification result on the current local bench:
  - `pytest -m smoke -n 2 -q`
  - exits early with a clear explanatory message instead of trying to create conflicting sessions on one emulator

## Update On 2026-04-16 (Shared Auth URL For Parallel Workers)

The token-based entry flow was prepared for parallel worker sharing.

Important design choice:
- this is implemented as pytest session bootstrap, not as “one test must run first”
- reason: under `pytest-xdist`, workers are separate processes and test ordering is not a safe synchronization mechanism

Current behavior:
- if `ONLINEDUKEN_ENTRY_MODE=token`, the controller process can resolve one shared auth URL from:
  - `B2B_AUTH_URL`
  - `B2B_OB_AUTH_TOKEN`
  - internal login endpoint env configuration
  - cached runtime auth file
  - `B2B_AUTH_FETCH_COMMAND`
- the resolved URL is normalized and cached in:
  - `artifacts/runtime/b2b_auth.json`
- the same URL is then passed into all xdist workers before test execution

This is now the intended base for future BrowserStack parallel smoke runs.

### Internal Login Variant

The project now also supports fetching the shared auth token or URL through an internal POST endpoint before worker startup.

Current supported envs:
- `B2B_INTERNAL_LOGIN_URL`
- `B2B_INTERNAL_CLIENT_ID`
- `B2B_INTERNAL_CLIENT_SECRET`
- `B2B_INTERNAL_GRANT_TYPE`

Expected response handling:
- ready auth URL -> use directly
- `ob_auth_token` / `token` / `access_token` -> convert into the standard `ob-auth-token` auth URL

### App Login Fallback

If the internal endpoint is unavailable, the framework can still try one real bootstrap session through the app.

Current idea:
- log in through the native app flow
- open `OnlineDuken`
- inspect `current_url`, `document.cookie`, `localStorage`, and `sessionStorage`
- if a reusable auth URL or token is found, convert it into the shared `B2B_AUTH_URL` and pass it to all workers

### Operational Context File

The practical operating details for this bootstrap flow are now also captured in:
- `C:\Users\Kanat\Documents\New project\INTERNAL_AUTH_SETUP.md`
- `C:\Users\Kanat\Documents\New project\.env.internal.example`

## Update On 2026-04-18 (QR Smoke Templates)

QR smoke planning was refined using two concrete business QR templates provided by the user:

- `common`
  - `https://public.test.onlinebank.kz/applink/b2b/distributor/101040002039/client/{client_bin}/invoiceId/{invoice_id}/amount/{amount}/invoiceTitle/{invoice_title}`
- `megapolis`
  - `https://homebank.kz/payments/megapolisKZ?contract={contract}&iin={client_bin}&amount={amount}`

Project outcome so far:
- QR PNG assets can now be generated directly from templates
- the smoke suite is structured to treat `common` and `megapolis` as separate QR cases
- both QR types require `CLIENT_BIN`
- live implementation still needs one device pass for:
  - QR scanner entry
  - gallery upload icon / flow
  - final native payment screen locators

## Update On 2026-04-18 (QR Local Flow Validated)

The QR smoke path was then implemented and validated locally as a real Appium flow.

Confirmed native path:
- `OnlineDuken` home -> native `QR` tab
- native `QR` scanner screen
- native gallery button
- Android Photo Picker
- native payment screen
- native `Оплатить` button

Confirmed native locators:
- QR tab:
  - `//*[@content-desc='QR']`
- QR gallery:
  - `kz.halyk.onlinebank.stage:id/gallery`
- payment action:
  - bottom native `android.widget.Button`
  - text observed as `Оплатить`

Important backend finding:
- with a dummy client BIN, tapping `Оплатить` produces toast:
  - `Неправильный ИИН/БИН клиента в QR`
- practical meaning:
  - the automation path is real and reaches backend validation
  - a valid `CLIENT_BIN` is still required for green QR smoke

Key artifacts:
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_photo_select_native.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_pay_click_generic_3s.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_payment_invalid_bin_toast.png`

## Update On 2026-04-18 (Local Two-Device Parallel Work)

Parallel work progressed from design into real local setup:
- second AVD clone created:
  - `Medium_Phone_Parallel`
- second emulator started:
  - `emulator-5556`
- second Appium server started:
  - `http://127.0.0.1:4725`
- worker/device mapping is now supported through:
  - `LOCAL_ANDROID_DEVICE_MATRIX`

Framework improvements made during this work:
- smoke fixtures now avoid eagerly constructing the shared session fixture during parallel runs
- WebView recovery was strengthened with:
  - route fallback for smoke sections
  - `WEBVIEW` reconnection when chromedriver loses DevTools connection

Current honest status:
- true local two-device parallel infrastructure exists
- but long local parallel runs are still not stable enough to call production-ready on this machine
- BrowserStack remains the preferred target for routine parallel CI smoke

## Update On 2026-04-18 (CI Push Smoke Toggle)

The CI strategy is now more concrete:
- `smoke.yml`
  - still runs smoke on push
  - now uses BrowserStack `token` entry mode
  - now runs with `pytest -n 2`
  - can be disabled temporarily with repository variable:
    - `ENABLE_PUSH_SMOKE=false`
- `manual.yml`
  - remains manual-only through `workflow_dispatch`
  - stays the intended entry point for regression/manual runs

## Suggested Prompt For Continuing In A New Chat

Use this in a new chat if needed:

```text
Continue the OnlineDuken E2E analysis from the handoff files in the repo/workspace.
Read:
- HANDOFF_ONLINEDUKEN.md
- HISTORY_CHRONOLOGY.md
- ARTIFACTS_INDEX.md
- TEST_CASES_SMOKE_DRAFT.md

Context:
- APK: C:\Users\Kanat\Downloads\halyk_bank_app.apk
- phone: 7772229999
- PIN: 0000
- SMS step accepts any numeric code

Goal:
- finalize smoke cases,
- create Appium + Page Object Model structure,
- prioritize payment-related flows first.
```

## Update On 2026-04-18 (Automatic Local Launcher)

- Added `scripts/run_local_smoke.ps1` as the main local launcher for Android smoke.
- The launcher now prepares the local stack automatically:
  - editable Python install
  - global Appium install if needed
  - `uiautomator2` driver install if needed
  - `adb` startup
  - emulator startup
  - fresh Appium startup on required ports
- Verified bootstrap state:
  - `adb devices` returns `emulator-5554`
  - `http://127.0.0.1:4723/status` returns ready
- Verified targeted token-mode smoke:
  - `test_smoke_onlineduken_entry`
  - `test_smoke_catalog_has_suppliers`
- The original local startup problem:
  - `Could not find a connected Android device in 20000ms`
  is now handled by the launcher/bootstrap layer.
- Current honest blocker for long local runs:
  - the emulator still intermittently hangs on `adb` commands like `shell ps -A`, `force-stop`, and hidden-api cleanup
  - when that happens, Appium can lose `WEBVIEW_kz.halyk.onlinebank.stage` and later fail session cleanup
  - this is currently a local emulator/adb stability issue, not a missing dependency/bootstrap issue

## Update On 2026-04-19 (QR Smoke And Full Smoke Revalidation)

- User provided the real QR test BIN:
  - `900423400509`
- QR smoke was re-run for both requested QR templates:
  - `common`
  - `megapolis`
- Both QR smoke tests are now green locally.

Important implementation correction:
- the QR payment flow does not always land on a simple `Оплата` screen
- the live native screen observed in the green run is `Подписание платежа`
- the actionable confirmation step is therefore a signing/payment submit action, not just the old generic `Оплатить` assumption

Latest QR-only result:
- `2 passed`

Then the full local smoke suite was re-run in token mode.

Latest full smoke result:
- `5 passed`
- `2 failed`
- `1 skipped`

Passed:
- `test_smoke_onlineduken_entry`
- `test_smoke_orders_navigation`
- `test_smoke_bonuses_navigation_and_history`
- `test_smoke_qr_payment_flow[qr-common]`
- `test_smoke_qr_payment_flow[qr-megapolis]`

Failed:
- `test_smoke_catalog_has_suppliers`
- `test_smoke_cart_and_order_creation`

Skipped:
- `test_smoke_invoice_payment_from_home`
  - because `INVOICE_REFERENCE` is not configured yet

Current interpretation:
- auth and QR are no longer the main blockers
- the remaining red area is centered on catalog DOM stabilization and catalog-dependent cart flow

Detailed run report:
- `C:\Users\Kanat\Documents\New project\SMOKE_RUN_REPORT_2026-04-19.md`

## Update On 2026-04-19 (Shared Session Strategy Implemented)

- Smoke strategy was reworked to avoid repeating a full phone/SMS/PIN login for every single test.
- Current intended split:
  - isolated `auth smoke`
  - shared-session `UI smoke`
  - separate shared-session `payments smoke`
- Practical behavior:
  - UI smoke now tries to return to `OnlineDuken` home between tests instead of creating a fresh session each time
  - payments smoke uses its own managed session so QR/payment-side state does not pollute the UI chain
  - if a shared session dies, the managed-driver layer can restart just that session
- QR handling was also tightened:
  - generated QR values are now unique per run
  - this protects the main QR happy path from accidentally reusing an old QR and falling into the business flow for re-signing an unfinished payment
- Live post-refactor validation:
  - `test_smoke_onlineduken_entry`
  - `test_smoke_orders_navigation`
  - `test_smoke_bonuses_navigation_and_history`
  - `test_smoke_qr_payment_flow[qr-common]`
  - `test_smoke_qr_payment_flow[qr-megapolis]`
  - result: `5 passed`
