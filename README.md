# OnlineDuken Mobile Automation

Hybrid mobile automation project for:
- `Halyk` stage Android APK
- `OnlineDuken` WebView flow
- local Android execution
- BrowserStack App Automate execution for Android and iOS-ready configuration

## Goals

- keep the project git-ready from day one;
- run `smoke` tests automatically on pushes;
- check test environment availability before running CI smoke;
- keep all other tests manual-only;
- support hybrid app automation:
  - native Android/iOS shell
  - WebView inside `OnlineDuken`
- preserve working context in versioned Markdown files so the project can be resumed without losing history

## Stack

- Python
- `pytest`
- `Appium`
- `Allure`
- BrowserStack App Automate

## Project Layout

```text
mobile_automation/
  config.py
  driver_factory.py
  healthcheck.py
  flows.py
  pages/
    native.py
    web.py
tests/
  smoke/
  manual/
.github/workflows/
```

Important context files in project root:
- `HANDOFF_ONLINEDUKEN.md`
- `HISTORY_CHRONOLOGY.md`
- `ARTIFACTS_INDEX.md`
- `TEST_CASES_SMOKE_DRAFT.md`
- `PROJECT_PROGRESS.md`
- `INTERNAL_AUTH_SETUP.md`
- `SMOKE_RUN_REPORT_2026-04-19.md`
- `BROWSERSTACK_RUN_REPORT_2026-04-27.md`

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements-ci.txt
pip install -e . --no-deps
```

3. Copy `.env.example` to `.env` and fill values.
4. For internal-auth / parallel setup, use `.env.internal.example` as the base template.

## Running Tests Locally

Recommended local launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_smoke.ps1 -Workers 1 -SafeSmoke
```

What this launcher does automatically:
- installs Python dependencies if needed
- installs Appium globally if missing
- installs the `uiautomator2` Appium driver if missing
- starts `adb`
- starts the Android emulator if it is not running
- starts fresh Appium server instances on the required ports
- exports local env vars such as `TARGET`, `PLATFORM`, `ONLINEDUKEN_ENTRY_MODE`, and `LOCAL_ANDROID_DEVICE_MATRIX`

Bootstrap only, without running tests:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_smoke.ps1 -Workers 1 -BootstrapOnly
```

Smoke:

```bash
pytest -m smoke
```

Latest verified full local smoke command:

```powershell
$env:TARGET='local'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:CLIENT_BIN='900423400509'
py -3.12 -m pytest -m smoke -q -s -ra
```

Latest verified QR-only smoke command:

```powershell
$env:TARGET='local'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:CLIENT_BIN='900423400509'
py -3.12 -m pytest tests\smoke\test_smoke_suite.py -k "qr_payment_flow" -q -s -ra
```

Parallel smoke on BrowserStack:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure
```

Important:
- local parallel execution is intentionally blocked when `TARGET=local`
- the current local setup uses one emulator/Appium device session, so `-n > 1` on the same emulator would be unstable rather than truly parallel
- the current safe-smoke design is parallel-ready for BrowserStack workers, where each worker gets its own isolated mobile session
- BrowserStack-safe smoke now defaults to `ONLINEDUKEN_ENTRY_MODE=full`, so every BrowserStack test performs a real app login instead of relying on deeplink/token entry
- token bootstrap stays available for local WebUI and future optimized runs, but it is not the default BrowserStack-safe path
- until a BrowserStack-ready build with explicit `OnlineDuken` WebView debugging is available, BrowserStack push smoke is intentionally split into native-shell checks only
- the core project direction remains hybrid:
  - BrowserStack-safe smoke now validates native shell reachability
  - full `OnlineDuken` WebView coverage continues to run locally and will later be re-enabled in BrowserStack

Manual:

```bash
pytest -m manual
```

## OnlineDuken Web Suite

A separate browser-based suite now exists for `OnlineDuken` so web coverage can continue independently from the mobile container.

Test file:
- [test_onlineduken_web_suite.py](C:\Users\Kanat\Documents\New%20project\tests\web\test_onlineduken_web_suite.py)

Current scope:
- authenticated home page load
- catalog page state
- orders page
- bonuses page and history link
- more page and cashier menu item

Marker:

```bash
pytest -m web
```

Run the full web suite locally:

```powershell
$env:WEB_HEADLESS='true'
py -3.12 -m pytest tests\web\test_onlineduken_web_suite.py -q -ra
```

Run a single browser test:

```powershell
$env:WEB_HEADLESS='true'
py -3.12 -m pytest tests\web\test_onlineduken_web_suite.py -k "home_page_loads" -q -ra -s
```

Authentication requirement:
- the web suite needs a valid `B2B_AUTH_URL` or `B2B_OB_AUTH_TOKEN`
- it can also use the existing shared auth bootstrap if internal auth is configured
- if no valid auth is available, the suite skips cleanly instead of failing with false negatives

## Allure Reporting

The project now supports `Allure` reporting on top of `pytest`.

How it works:
- run tests with `--alluredir=allure-results`
- `pytest` writes raw Allure result files into `allure-results/`
- then `Allure CLI` renders those files into a readable HTML report

Automatic attachments for failed tests:
- mobile screenshot
- page source
- driver metadata:
  - session id
  - current context
  - available contexts
  - current package / activity when available
  - current URL when available
- pytest failure text

When `--alluredir` is used, the project also writes `environment.properties` so the report shows:
- `TARGET`
- `PLATFORM`
- `ONLINEDUKEN_ENTRY_MODE`
- BrowserStack/local context

### Install Allure Locally

The Python plugin is installed with the project:

```bash
pip install -e .
```

You still need the `Allure CLI` locally to open HTML reports.

Typical Windows options:
- `choco install allure-commandline`
- `scoop install allure`

### Run Tests With Allure

Plain smoke run with Allure:

```powershell
$env:TARGET='local'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='token'
py -3.12 -m pytest -m smoke --alluredir=allure-results
```

Safe smoke through the local launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_smoke.ps1 -Workers 1 -SafeSmoke -Allure
```

### Open the Report

Temporary local server:

```bash
allure serve allure-results
```

Static HTML output:

```bash
allure generate allure-results --clean -o allure-report
allure open allure-report
```

### CI Direction

Recommended CI usage:
- run pytest with `--alluredir=allure-results`
- upload `allure-results` as a workflow artifact
- optionally generate `allure-report` in a separate CI step

This fits the current strategy:
- push -> smoke
- manual workflow -> regression / custom runs

Single platform examples:

```bash
$env:TARGET='local'
$env:PLATFORM='android'
pytest -m smoke
```

Fast `OnlineDuken` entry by auth URL/token:

```bash
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:B2B_AUTH_URL='https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=...'
pytest tests/smoke/test_smoke_suite.py::test_smoke_onlineduken_entry -q -s
```

You can also provide only the token:

```bash
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:B2B_OB_AUTH_TOKEN='...'
pytest -m smoke
```

### What `B2B_AUTH_URL` / bootstrap means

`B2B_AUTH_URL` is a fully prepared `OnlineDuken` authentication URL, for example:

```text
https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=...
```

The framework can also accept only the token itself through `B2B_OB_AUTH_TOKEN` and build the full URL automatically.

In practical terms this URL is a reusable shortcut into the authenticated `OnlineDuken` web flow. It helps us avoid repeating the full web authorization sequence for every smoke test worker.

`bootstrap` means the one-time step where the framework tries to obtain that reusable auth URL before the rest of the suite starts.

Bootstrap sources are checked in this order:
- direct env values: `B2B_AUTH_URL` or `B2B_OB_AUTH_TOKEN`
- cached runtime auth URL from `artifacts/runtime/b2b_auth.json`
- internal auth endpoint
- custom fetch command
- one real mobile login through the app, followed by extraction of a reusable auth URL from the opened `OnlineDuken` session

Why this matters:
- the first successful login can produce one reusable auth URL
- pytest injects the same normalized auth URL into all parallel workers
- later tests can reuse that auth URL instead of redoing phone, SMS, PIN, and in-WebView auth every time

Important limitation:
- auth bootstrap speeds up authentication reuse
- it does **not** replace a BrowserStack build that lacks explicit `OnlineDuken` WebView debugging
- if BrowserStack cannot expose the real in-app `WEBVIEW_kz.halyk.onlinebank.stage`, token reuse still helps with auth, but hybrid WebView automation will remain limited until the APK exposes the debuggable webview correctly

Internal login endpoint bootstrap:

```bash
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:TARGET='browserstack'
$env:B2B_INTERNAL_LOGIN_URL='https://testapi.onlinebank.kz/internal/internal/users/login-user-by-id-and-contract/...?...'
$env:B2B_INTERNAL_CLIENT_ID='...'
$env:B2B_INTERNAL_CLIENT_SECRET='...'
pytest -m smoke -n 2
```

This path posts `client_id`, `client_secret`, and `grant_type=internal`, then tries to extract either:
- a ready auth URL
- `ob_auth_token`
- `token`
- `access_token`

If only a token is returned, the framework converts it into:
- `https://b2b.test.onlinebank.kz/web/customer-frontend/auth?ob-auth-token=...`

Auth URLs are validated before caching. The framework accepts only real auth URLs with `/web/customer-frontend/auth` and `ob-auth-token`; generic `customer-frontend` routes are rejected so workers do not reuse an unauthenticated shell by mistake.

## BrowserStack Split

Current BrowserStack strategy is intentionally split because `App Automate` cannot yet switch into the `OnlineDuken` `WEBVIEW` for the current uploaded stage builds.

What runs in BrowserStack right now:
- `browserstack_safe` native smoke
- full native login in every BrowserStack test session
- native main app home check
- native entry into the `OnlineDuken` container
- parallel execution with `pytest-xdist`, default demo target: `-n 3`

What stays out of BrowserStack smoke for now:
- all tests marked `webview`
- payment flows marked `payments`

Control flag:

```bash
BROWSERSTACK_WEBVIEW_ENABLED=false
```

When a new build arrives with explicit `WebView.setWebContentsDebuggingEnabled(true)` for `OnlineDuken`, this flag can be turned on and BrowserStack smoke can be expanded back toward the hybrid baseline.

Recommended BrowserStack demo command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure
```

This command uses:
- `TARGET=browserstack`
- `PLATFORM=android`
- `ONLINEDUKEN_ENTRY_MODE=full`
- `B2B_SHARED_AUTH_BOOTSTRAP=false`
- `BROWSERSTACK_WEBVIEW_ENABLED=false`
- `BROWSERSTACK_LOGIN_STAGGER_SEC=20`
- marker expression `smoke and browserstack_safe and not manual`

Why login staggering exists:
- current BrowserStack-safe smoke uses one test phone across workers
- if two workers request OTP at the same time, one session can receive `Истек код для авторизации`
- staggering keeps the run xdist/BrowserStack-parallel but avoids same-user OTP races
- the best long-term improvement is a pool of test users, one per parallel worker

### BrowserStack SDK / browserstack.yml Position

BrowserStack officially recommends the SDK path with a root-level `browserstack.yml` and `browserstack-sdk pytest`. A prepared `browserstack.yml` is included for that future path.

Current project decision:
- keep the direct Appium + pytest path as the primary stable path for now
- use `browserstack.yml` as an optional migration layer, not as the only way to run tests
- revisit SDK adoption after BrowserStack-safe smoke is consistently green and the team decides whether Test Observability / SDK-managed uploads are worth the extra abstraction

Reason:
- our direct path already handles project-specific markers, fallback login, Allure, environment healthcheck, BrowserStack-safe splitting, and CI toggles
- the SDK can simplify BrowserStack reporting and config, but it also adds another wrapper that can obscure failures while we are still stabilizing the mobile flow

## How To Re-enable Full BrowserStack Hybrid Smoke

When a new Android build is delivered with explicit `OnlineDuken` WebView debugging enabled, use this checklist to return BrowserStack from the temporary native-shell split back to the full hybrid baseline.

### 1. Update the uploaded app

- upload the new APK to BrowserStack
- replace `BROWSERSTACK_APP_ANDROID` in GitHub Secrets or local `.env`

### 2. Turn WebView mode back on

Set:

```bash
BROWSERSTACK_WEBVIEW_ENABLED=true
```

Places to update if you want BrowserStack full hybrid mode by default:
- local `.env`
- GitHub Actions env in [smoke.yml](C:\Users\Kanat\Documents\New%20project\.github\workflows\smoke.yml)
- GitHub Actions env in [manual.yml](C:\Users\Kanat\Documents\New%20project\.github\workflows\manual.yml)

### 3. Validate with a minimal BrowserStack WebView probe

Run only the entry test first:

```bash
pytest tests/smoke/test_smoke_suite.py -k "onlineduken_entry" -q -s
```

Expected result:
- BrowserStack session starts
- `OnlineDuken` opens
- framework switches from `NATIVE_APP` to `WEBVIEW`

### 4. Expand BrowserStack smoke markers

Current temporary push workflow runs:

```bash
pytest -m "smoke and browserstack_safe and not manual" -n 3 --alluredir=allure-results
```

To return to the full hybrid BrowserStack smoke, change it back to:

```bash
pytest -m "smoke and not manual" -n 3 --alluredir=allure-results
```

### 5. Re-check deferred BrowserStack flows

After WebView is confirmed, re-validate in this order:
- `test_smoke_onlineduken_entry`
- `test_smoke_catalog_has_suppliers`
- `test_smoke_orders_navigation`
- `test_smoke_bonuses_navigation_and_history`
- payment and QR flows

### 6. Keep the temporary split only if the probe still fails

If BrowserStack still cannot switch to `WEBVIEW`, revert only the app reference and keep:
- `BROWSERSTACK_WEBVIEW_ENABLED=false`
- BrowserStack marker expression:
  - `smoke and browserstack_safe and not manual`

This lets BrowserStack stay green while local hybrid coverage continues to prove the full product flow.

QR smoke generation:
- the project can now generate QR PNG assets from templates instead of requiring a manually prepared file
- supported QR smoke template types:
  - `common`
  - `megapolis`
- required business input:
  - `CLIENT_BIN`
- optional QR template inputs:
  - `QR_AMOUNT`
  - `QR_INVOICE_ID`
  - `QR_INVOICE_TITLE`
  - `QR_MEGAPOLIS_CONTRACT`
- current local QR smoke implementation:
  - enters `OnlineDuken`
  - opens the native `QR` tab
  - taps the native gallery button
  - selects the first image from Android Photo Picker
  - waits for the native payment screen
  - taps the primary action on the native signing/payment screen
  - verifies transition to the confirmation stage
- latest validated local QR result with `CLIENT_BIN=900423400509`:
  - `common` -> passed
  - `megapolis` -> passed
- QR payloads are generated with unique numeric values per run so the main QR smoke does not accidentally reuse an old QR and fall into the business flow for re-signing a pending payment
- current BrowserStack note:
  - local gallery upload is implemented
  - BrowserStack media upload still needs a dedicated upload path before QR smoke can run there end-to-end

Local multi-device parallel example:

```bash
$env:LOCAL_ANDROID_DEVICE_MATRIX='emulator-5554|http://127.0.0.1:4723;emulator-5556|http://127.0.0.1:4725'
$env:ONLINEDUKEN_ENTRY_MODE='token'
pytest -m smoke -n 2
```

Current practical note:
- the project now supports worker-to-device mapping for real local parallel runs
- on this machine, a second local AVD/Appium slot was brought up successfully
- however, long local parallel runs are still less stable than desired, so BrowserStack remains the preferred target for routine parallel smoke

Shared token bootstrap for parallel workers:

```bash
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:TARGET='browserstack'
$env:B2B_AUTH_FETCH_COMMAND='powershell -File .\\scripts\\print_b2b_auth_url.ps1'
pytest -m smoke -n 2
```

Fallback order for shared auth bootstrap:
- internal login endpoint
- `B2B_AUTH_FETCH_COMMAND`
- one bootstrap login through the mobile app with token extraction from `WebView`
- runtime cache

How it works:
- the auth URL is resolved once in the pytest controller process before workers start
- the resolved URL is cached in `artifacts/runtime/b2b_auth.json`
- the same normalized `B2B_AUTH_URL` is injected into each parallel worker
- this is intentionally implemented as session bootstrap, not as a “first test”, because test ordering is fragile under `xdist`

The project normalizes the auth URL automatically:
- adds `lang=ru` if missing
- adds `navigateTo=home` if missing

For local runs, Appium is started automatically by the test session fixture.
No separate manual Appium server start is required if:
- `APPIUM_NODE_PATH` is valid
- `APPIUM_MAIN_JS` is valid
- `ANDROID_SDK_ROOT` / `ANDROID_HOME` are valid
- the Android emulator/device is available

Current practical note for local Android:
- the launcher now fixes the original `Could not find a connected Android device in 20000ms` problem by preparing the local device/Appium stack automatically
- however, long local runs may still hit emulator-level `adb` hangs on commands like `shell ps -A`
- when that happens, the next stabilization step is a fresh emulator restart, because the blocker is below the pytest/Appium project layer

```bash
$env:TARGET='browserstack'
$env:PLATFORM='android'
pytest -m smoke
```

## CI Strategy

- `smoke.yml`
  - runs on push
  - checks environment availability first
  - runs only `smoke and browserstack_safe and not manual`
  - uses full app login and `pytest -n 3`
  - uploads raw `allure-results` as a GitHub Actions artifact
  - can be disabled temporarily with repository variable `ENABLE_PUSH_SMOKE=false`
  - can still be forced manually through `workflow_dispatch`
- `manual.yml`
  - runs only via `workflow_dispatch`
  - can run `manual`, `smoke`, or custom marker expressions
  - uses `pytest -n 3` and uploads raw `allure-results`
  - is the intended path for regression/manual suites

## Smoke Execution Model

- `auth smoke`
  - isolated session
  - verifies login and `OnlineDuken` entry
- `UI smoke`
  - one shared long-lived session
  - reuses one login for navigation/read-only checks
  - attempts recovery back to `OnlineDuken` home between tests instead of relogging every time
- `payments smoke`
  - separate shared long-lived session
  - reuses one login for QR and later payment scenarios
  - can recover the payment session and, if needed, restart only that session without poisoning the UI smoke chain

## Latest Smoke Status

Latest local full smoke validation on `2026-04-19`:
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
  - missing `INVOICE_REFERENCE`

Detailed report:
- `SMOKE_RUN_REPORT_2026-04-19.md`

Additional validation after the shared-session refactor:
- `test_smoke_onlineduken_entry`
- `test_smoke_orders_navigation`
- `test_smoke_bonuses_navigation_and_history`
- `test_smoke_qr_payment_flow[qr-common]`
- `test_smoke_qr_payment_flow[qr-megapolis]`
- latest result:
  - `5 passed`

## Current Assumptions

- Android login credentials:
  - phone `7772229999`
  - SMS can be any numeric code
  - PIN `0000`
- OnlineDuken is reached through:
  - app login
  - deep link
  - passcode unlock
- An additional fast entry mode is supported:
  - `ONLINEDUKEN_ENTRY_MODE=token`
  - use `B2B_AUTH_URL` or `B2B_OB_AUTH_TOKEN`
  - auth URLs are normalized to include `lang=ru` and `navigateTo=home`
  - do not commit real tokens into git
- WebView route base:
  - `https://b2b.test.onlinebank.kz/web/customer-frontend/`

## Notes

- BrowserStack credentials must be supplied through GitHub Secrets in CI.
- The environment precheck is intentionally externalized into a reusable Python module.
- Payment flows are included in the smoke suite structure, but some of them require stable QR/invoice test data to be fully green.
- `pytest-xdist` is included for BrowserStack-style parallel runs.
- push smoke now has a repo-variable kill switch:
  - set `ENABLE_PUSH_SMOKE=false` to stop automatic smoke on pushes temporarily
- `Settings` now reads environment values at instantiation time, so runtime-injected values such as shared token auth URLs are visible to workers and fixtures.
- a built-in internal-login bootstrap is available for environments where the auth token must be fetched from a private API before parallel runs
- QR smoke now supports template-driven asset generation for `common` and `megapolis` QR cases
- QR smoke is now implemented locally through native QR scanner + gallery upload + native payment tap
- `PROJECT_PROGRESS.md` should be updated whenever project structure, strategy, smoke coverage, or important discoveries change.
- Historical context from the APK research phase is intentionally stored in Markdown files in the repository and should not be deleted.
- Internal auth bootstrap details are summarized in `INTERNAL_AUTH_SETUP.md`.
