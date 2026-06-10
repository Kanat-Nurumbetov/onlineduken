# Project Progress

## Purpose

This is the live project status file.

It should be updated as the project evolves so that:
- context is not lost between sessions;
- work can be resumed from another device or another chat;
- changes in strategy are documented in one place;
- current implementation status is clear without rereading the full history.

Use this together with:
- `HANDOFF_ONLINEDUKEN.md` for big-picture context
- `HISTORY_CHRONOLOGY.md` for the full request timeline
- `ARTIFACTS_INDEX.md` for saved evidence
- `TEST_CASES_SMOKE_DRAFT.md` for smoke scope

## Current Status

As of `2026-04-16`:

- APK analysis phase is complete enough to start automation.
- Login flow and `OnlineDuken` entry were explored.
- `OnlineDuken` was confirmed as a `WebView` inside native `B2BActivity`.
- Main business routes inside the WebView were identified.
- A local automation project scaffold has been created.
- Local start strategy was refined: Appium should be started programmatically from the test session for `local` runs instead of relying on a separately launched background shell process.
- Local smoke login flow was advanced further:
  - SMS step is handled
  - passcode keypad entry for `0000` is automated
  - post-login `Далее` prompt is handled
  - store selection popup should choose the first available store
- The current blocker is now local Android infrastructure stability:
  - `adb` intermittently hangs on simple shell calls against `emulator-5554`
  - Appium then times out while reading device properties or enumerating webviews
  - because of this, local smoke is currently blocked by emulator/adb health rather than by test-flow logic alone

## What Is Already Implemented

### Documentation

- historical handoff and research documents are stored in project root
- smoke draft exists
- artifact index exists
- this live progress file now exists

### Automation foundation

- Python project with `pytest`
- Appium driver factory
- local execution path
- BrowserStack execution path
- env-based configuration
- test environment healthcheck helper
- native page object placeholders
- web page object placeholders
- smoke test skeleton
- manual test placeholder
- GitHub Actions workflow separation:
  - push-triggered smoke
  - manual-triggered custom runs
- local Appium startup config wired through environment variables

## Current Test Strategy

### CI

- only `smoke` runs on push
- smoke must first check environment availability
- if the environment is down, smoke should not proceed blindly

### Manual

- non-smoke scenarios must run manually only
- deep exploratory tests and unstable business flows should stay out of push CI until stabilized

### Platform direction

- Android is the first active platform
- BrowserStack support is prepared for both Android and iOS
- iOS still needs real application package/data and flow validation before being made active

## Smoke Coverage Status

### Implemented as structure

- OnlineDuken entry
- catalog visibility
- orders navigation
- bonuses navigation
- QR payment skeleton
- invoice payment skeleton
- cart/order skeleton

### Not fully production-ready yet

- QR payment final implementation
- invoice payment final implementation
- cart and order creation final implementation
- deep WebView interactions beyond basic route-level checks

Reason:
- stable test data is still needed
- some deeper business screens need one more live locator pass

## Known Technical Facts

- Android package: `kz.halyk.onlinebank.stage`
- entry to OnlineDuken can be reproduced through deep link:
  - `https://halyk.onlinebank.kz/appLink/b2b/`
- passcode used during current research:
  - `0000`
- SMS step currently accepts any numeric code in test environment
- OnlineDuken base route:
  - `https://b2b.test.onlinebank.kz/web/customer-frontend/`

## Open Items

### Test data still needed

- stable QR image for gallery-based QR payment smoke
- stable invoice reference/data for invoice payment smoke
- stable supplier/product combination for cart/order smoke
- if needed later, stable iOS app artifact for BrowserStack

### Functional confirmations still needed

- exact business path for contract selection ending with `376`
- preferred supplier for smoke tests
- final expected outcome for payment success assertions
- exact UI path to bonus history in the live app
- confirmation of stable local emulator/adb behavior before continuing full local smoke implementation

## Recommended Next Steps

1. Fill `.env` for local development.
2. Restore healthy local Android automation state:
   - ensure `adb` responds quickly to basic shell commands on `emulator-5554`
   - restart the emulator and/or adb if needed
3. Re-run the entry smoke after emulator stabilization.
4. Validate the store-selection popup path in a healthy session.
5. Add BrowserStack secrets in GitHub.
6. Stabilize payment-related locators and assertions.
7. Only then enable payment smoke paths fully in push CI.

## Maintenance Rule

Update this file after:
- project structure changes
- new workflows are added
- smoke scope changes
- major locators or routes are confirmed
- BrowserStack strategy changes
- a new blocking issue is found

## Update On 2026-04-20 (Cart Smoke Deferred)

- Cart-related smoke coverage is intentionally deferred for now.
- Both cart flows are left in the test suite but are explicitly skipped with a stable reason:
  - catalog -> supplier -> product -> cart -> create order
  - home product -> cart -> create order
- Reason:
  - the current test environment does not yet have a stable supplier with predictable category, subcategory, and product data for reliable cart/order assertions
  - exploratory probes showed that at least one supplier route reaches categories but then lands on an empty subcategory state, which is not good enough for deterministic smoke
- Practical decision:
  - keep catalog smoke as a page-availability/navigation check
  - keep QR/payment and non-mutating UI smoke active
  - re-enable cart smoke after the user prepares a stable supplier specifically for automation

## Update On 2026-04-20 (Allure Reporting Added)

- `Allure` reporting was added on top of the current `pytest` project.
- Integration now includes:
  - `allure-pytest` dependency in the project
  - smoke tests labeled with `epic / feature / story / title`
  - QR flow split into readable `Allure` steps
  - failed tests automatically attaching:
    - screenshot
    - page source
    - driver metadata
    - pytest failure text
  - auto-generated `environment.properties` when tests are run with `--alluredir`
- Local launcher support was added:
  - `scripts/run_local_smoke.ps1 -Allure`
- Practical result:
  - existing console output and artifact behavior remain useful
  - `Allure` becomes the readable report layer for local work and future CI artifacts

## Update On 2026-04-20 (BrowserStack Connectivity Verified)

- Real BrowserStack App Automate connectivity was verified against:
  - project: `B2B Mobile Demo`
  - app: `bs://2824992f98ef03a4740dc5931569b2838d5a5ce6`
  - device: `Samsung Galaxy S24`
  - Android version: `14.0`
- The framework was adjusted so BrowserStack authentication works for raw Appium sessions.
- Actual BrowserStack sessions were created successfully for both:
  - single-session connectivity check
  - parallel `pytest -n 2` smoke check
- Current BrowserStack-specific blocker:
  - `OnlineDuken` entry fails while switching to `WEBVIEW`
  - BrowserStack Appium returns errors such as:
    - `Failed to get sockets matching: @webview_devtools_remote_*`
    - `make sure the app has its WebView configured for debugging`
- Interpretation:
  - BrowserStack access, app upload reference, and remote session creation are working
  - the remaining blocker is hybrid WebView automation on BrowserStack, not account connectivity
- Relevant BrowserStack runs captured on `2026-04-20`:
  - build `local-connect-check-20260420`
  - build `local-parallel-check-20260420`

## Update On 2026-04-21 (BrowserStack Smoke Split)

- BrowserStack smoke is now intentionally split from the local hybrid smoke baseline.
- Reason:
  - BrowserStack `App Automate` still cannot switch the current stage builds into the `OnlineDuken` `WEBVIEW`
  - the blocking error remains `Failed to get sockets matching: @webview_devtools_remote_*`
- Practical decision:
  - keep the overall project foundation hybrid
  - keep local smoke and future BrowserStack target state centered on native + WebView automation
  - but run only `browserstack_safe` native-shell checks in BrowserStack until a build with explicit `WebView.setWebContentsDebuggingEnabled(true)` for `OnlineDuken` is available
- New BrowserStack-safe scope:
  - app shell is reachable
  - native `OnlineDuken` container is reachable
- Current BrowserStack controls:
  - marker: `browserstack_safe`
  - env flag: `BROWSERSTACK_WEBVIEW_ENABLED=false`
- Verification result:
  - BrowserStack-safe smoke was run in parallel with `pytest -m "smoke and browserstack_safe" -n 2`
  - result: `2 passed`
- Recovery path is now documented in `README.md`:
  - upload the new APK
  - set `BROWSERSTACK_WEBVIEW_ENABLED=true`
  - probe `onlineduken_entry`
  - switch workflow marker expression back to full smoke

## Update On 2026-04-21 (Separate OnlineDuken Web Suite Added)

- A dedicated browser-based `OnlineDuken` suite was added so web coverage can continue even while BrowserStack hybrid automation is split.
- New implementation pieces:
  - `mobile_automation/web_driver_factory.py`
  - `mobile_automation/web_flows.py`
  - `tests/web/test_onlineduken_web_suite.py`
- New marker:
  - `web`
- Current browser-suite coverage:
  - authenticated home page load
  - catalog state
  - orders page
  - bonuses page and history link
  - more page
- Validation status:
  - test collection passes
  - a live browser run currently skips cleanly when no valid `B2B_AUTH_URL` / `B2B_OB_AUTH_TOKEN` is present in the local environment

## Update On 2026-04-22 (Auth Bootstrap Clarified And Main-First Entry Tightened)

- The meaning of `B2B_AUTH_URL` and shared auth bootstrap was clarified and documented more explicitly.
- Practical interpretation:
  - `B2B_AUTH_URL` is the reusable authenticated `OnlineDuken` URL
  - `B2B_OB_AUTH_TOKEN` is only the token portion used to build that URL
  - `bootstrap` is the one-time resolution step that obtains one reusable auth URL before parallel workers start
- The framework already supports these bootstrap sources:
  - direct env URL/token
  - cached runtime auth URL
  - internal auth endpoint
  - custom fetch command
  - one real app login followed by auth extraction from the opened `OnlineDuken` session
- BrowserStack-safe smoke was tightened so the native-shell test no longer stops at the phone field alone:
  - it now completes login when needed
  - it verifies that the real native main home becomes reachable
  - it still remains inside the BrowserStack-safe native scope
- `OnlineDuken` token-mode entry was also tightened:
  - a generic foreign `WEBVIEW_*` context is no longer treated as success by itself
  - this prevents false positives such as non-app webview shells from being mistaken for the real in-app `OnlineDuken` container
  - when token-mode cannot open the target container directly, the flow now falls back to the normal app path:
    - complete login
    - reach main home
    - select the expected contract
    - open `OnlineDuken` from the main screen
- This moves the implementation closer to the intended business flow:
  - first real login through the app
  - then reuse the resolved auth URL across later smoke workers and sessions

## Update On 2026-04-22 (BrowserStack Safe Smoke Green Again)

- The BrowserStack-safe smoke pack was revalidated with a real parallel cloud run.
- Successful command:
  - `pytest tests\smoke\test_smoke_suite.py -k "browserstack_safe" -n 2 -q -s -ra`
- Effective runtime configuration:
  - `TARGET=browserstack`
  - `PLATFORM=android`
  - `ONLINEDUKEN_ENTRY_MODE=token`
  - `BROWSERSTACK_WEBVIEW_ENABLED=false`
  - `BROWSERSTACK_APP_ANDROID=bs://c275dbb0208fb6c0f990a5433bf793fe9f5329dc`
- Result:
  - `2 passed`
- BrowserStack build details:
  - build name: `codex-browserstack-safe-20260422-run3`
  - hashed id: `2dd4beae65ea70b47243c30299a2589f948b0b8c`
- Report saved to:
  - `artifacts/browserstack/codex-browserstack-safe-20260422-run3/REPORT.md`
- Final fixes that made this run green:
  - BrowserStack-safe login now completes the real auth flow up to native main home
  - token-mode `OnlineDuken` entry rejects unrelated foreign webview contexts
  - SMS confirmation and PIN entry are now treated as different native states
  - PIN entry has a direct-input fallback for remote-device layouts where keypad bounds are not present

## Update On 2026-04-16 (Context Split)

- `OnlineDuken` should now be treated as a mixed flow, not as pure `WebView`.
- User-confirmed native screens inside `OnlineDuken`:
  - QR flow
  - gallery picker used for QR upload
  - cashier page
  - all nested screens inside cashier functionality
- Everything else inside `OnlineDuken` should be treated as `WebView` unless a future capture proves otherwise.
- Practical automation rule:
  - default to `WEBVIEW_kz.halyk.onlinebank.stage` after entering `OnlineDuken`
  - switch back to `NATIVE_APP` only for QR, gallery/system picker, and cashier flow
- Native home entry was stabilized through the real `OnlineDuken` shortcut.
- The contract currently used on native home is `name050201.705376`.
- The first captured store in the `OnlineDuken` store-selection popup is:
  - `QQQQQ`
  - `0455b1fd-7001-4417-ac6c-f3897d98bce8`

## Update On 2026-04-16 (Safe Smoke Attempt)

- A safe local smoke subset was attempted for:
  - `OnlineDuken` entry
  - catalog visibility
  - orders navigation
  - bonuses navigation/history
- Payments, QR, and cart/order creation were intentionally excluded from this run.
- The current blocking issue for the safe subset is not WebView navigation itself.
- The current blocking issue is that after login the app intermittently leaves the expected native home flow and lands in the Android launcher (`.NexusLauncherActivity`) instead of `MainActivity`.
- Because of that, all four safe smoke tests currently fail before the `OnlineDuken` shortcut can be opened.
- Recovery logic was added for:
  - returning from `QrActivity`
  - re-activating the app if focus moves outside `kz.halyk.onlinebank.stage`
  - non-blocking fallback when contract suffix `376` is not found immediately
- Latest relevant failure artifacts:
  - `artifacts/main_home_not_detected.png`
  - `artifacts/main_home_not_detected.xml`
  - `artifacts/main_home_not_detected.txt`

## Update On 2026-04-16 (Safe Smoke Stabilized)

- The local safe smoke subset now passes end-to-end:
  - `OnlineDuken` entry
  - catalog visibility
  - orders navigation
  - bonuses navigation and history visibility
- Latest passing local run result:
  - `4 passed in 129.02s`
- The safe smoke subset is intentionally still limited to non-payment flows:
  - no `QR`
  - no invoice payment
  - no cart/order creation
- A shared Appium session is now used for the safe smoke subset instead of creating a fresh mobile session for every one of these tests.
- Reason for the shared session change:
  - repeated local session teardown was causing `adb` and Appium instability
  - single-session smoke is materially faster and more stable for the current APK/test bench
- Entry stabilization changes that are now in place:
  - `enter_onlineduken` no longer hard-fails before trying deeplink fallback when native home is flaky
  - native shortcut open failures can now fall through to the next entry strategy
  - the store-selection popup in `WebView` is detected and the first store is selected automatically
- Confirmed current WebView DOM facts used by the smoke implementation:
  - home route: `/web/customer-frontend/`
  - catalog route: `/web/customer-frontend/distributor`
  - bonuses route: `/web/customer-frontend/bonuses`
  - bonus history entry is a `div.card.card-item[routerlink="./history"]`
- Current practical note for catalog:
  - the primary path still clicks the `Каталог` tab
  - if the DOM does not settle fast enough after the click, the smoke test falls back to direct route open for `/web/customer-frontend/distributor`
- New useful probe artifacts generated during stabilization:
  - `artifacts/webview_after_onlineduken_entry.html`
  - `artifacts/webview_after_onlineduken_entry.png`
  - `artifacts/bonuses_page_probe.html`
  - `artifacts/bonuses_page_probe.png`
  - `artifacts/catalog_page_probe.html`
  - `artifacts/catalog_page_probe.png`

## Update On 2026-04-16 (Token Entry Mode Added)

- A new `OnlineDuken` entry mode was added:
  - `ONLINEDUKEN_ENTRY_MODE=token`
- New config inputs:
  - `B2B_AUTH_URL`
  - `B2B_OB_AUTH_TOKEN`
- Important technical finding:
  - the URL `https://b2b.test.onlinebank.kz/web/customer-frontend/auth?...` is not resolved by Android as a direct app link for package `kz.halyk.onlinebank.stage`
  - because of that, token mode does not open the app directly from this URL at the Android intent level
- Current token-mode strategy:
  - try direct auth URL deep link first
  - if Android cannot resolve it, fall back to opening the `OnlineDuken` container
  - once `WEBVIEW` is available, load the token auth URL inside the `WebView`
- Verified result:
  - token-based `OnlineDuken` entry smoke passed locally
  - latest entry-only result:
    - `1 passed in 110.04s`
- Practical implication:
  - the token is useful for bypassing `WebView` auth inside `OnlineDuken`
  - but it does not fully replace Android-level app entry on a cold start

## Update On 2026-04-16 (Token Mode Stabilized)

- Token mode was stabilized further by normalizing the auth URL automatically:
  - `lang=ru`
  - `navigateTo=home`
- This matters because a bare URL like:
  - `/web/customer-frontend/auth?ob-auth-token=...`
  was loading only the auth shell and navbar, not a fully usable `OnlineDuken` home state.
- After URL normalization, the local safe smoke subset also passes in token mode.
- Latest passing token-mode result:
  - `4 passed in 103.88s`
- Practical current outcome:
  - classic full-entry safe smoke is green
  - token-entry safe smoke is also green
  - token mode is now the better candidate for faster local runs and future parallelization work

## Update On 2026-04-16 (Parallel-Ready Baseline)

- `pytest-xdist` was added to the project dependencies.
- The project is now explicitly prepared for parallel smoke execution on BrowserStack.
- A protective guard was added for local runs:
  - if `pytest -n ...` is requested while `TARGET=local`, the session exits early with a clear message
  - reason: the current local setup uses a single emulator/Appium device session, so parallel workers on one emulator would create unstable contention rather than real parallel coverage
- Practical current rule:
  - local Android runs stay sequential
  - BrowserStack is the intended path for true parallel smoke execution
- The protection was verified with a real command:
  - `pytest -m smoke -n 2 -q`
  - current result on local setup: early exit with a clear message instead of unstable Appium/device contention
- Python tooling alignment note:
  - `pytest.exe` on this machine uses Python `3.12`
  - editable install and `pytest-xdist` were also installed into that same interpreter so plugin loading is now consistent

## Update On 2026-04-16 (Shared Token Bootstrap)

- Parallel token-mode execution design was refined:
  - instead of making one test run first and feed the others, the project now resolves the auth URL once in the pytest controller process before worker startup
  - this avoids fragile test ordering and cross-worker dependencies under `xdist`
- New runtime auth options:
  - `B2B_AUTH_FETCH_COMMAND`
  - `B2B_SHARED_AUTH_BOOTSTRAP`
  - `B2B_AUTH_CACHE_TTL_SEC`
  - `B2B_AUTH_CACHE_PATH`
- Behavior:
  - if token mode is enabled, pytest can resolve one shared auth URL from env, cache, or a fetch command
  - the resolved URL is normalized and stored in `artifacts/runtime/b2b_auth.json`
  - the same auth URL is injected into every pytest worker
- Internal config improvement:
  - `Settings` now reads env values at instantiation time rather than freezing them at import time
  - this is important for worker-specific runtime values such as shared auth bootstrap data

## Update On 2026-04-16 (Internal Login Endpoint Bootstrap)

- The shared token bootstrap can now fetch auth data directly from an internal API endpoint.
- New env options:
  - `B2B_INTERNAL_LOGIN_URL`
  - `B2B_INTERNAL_CLIENT_ID`
  - `B2B_INTERNAL_CLIENT_SECRET`
  - `B2B_INTERNAL_GRANT_TYPE`
- Expected request shape:
  - `POST` with form fields `client_id`, `client_secret`, `grant_type`
- Response handling:
  - if the endpoint returns a ready auth URL, the framework uses it directly
  - if the endpoint returns `ob_auth_token`, `token`, or `access_token`, the framework converts it into the standard `ob-auth-token` auth URL
- Practical use:
  - this is now the preferred parallel bootstrap path when a private internal auth API is available

## Update On 2026-04-16 (App Login Fallback For Shared Token)

- If the private internal login endpoint is unavailable, shared token bootstrap now has another fallback:
  - start one bootstrap mobile session
  - authenticate through the real app flow
  - enter `OnlineDuken`
  - try to extract a reusable auth URL or token from the active `WebView`
- New env option:
  - `B2B_APP_AUTH_BOOTSTRAP`
- Current bootstrap priority is now:
  - internal login endpoint
  - `B2B_AUTH_FETCH_COMMAND`
  - app login bootstrap
  - cached runtime auth URL

## Update On 2026-04-16 (Context Locked In)

- Added a dedicated internal-auth context file:
  - `INTERNAL_AUTH_SETUP.md`
- Added a ready local template for parallel/token/bootstrap configuration:
  - `.env.internal.example`
- Added extra ignore rules for local secret-bearing env files:
  - `.env.local`
  - `.env.parallel.local`
- Practical outcome:
  - the project now contains both implementation and written operating context for internal token bootstrap and fallback behavior

## Update On 2026-04-18 (QR Templates Added)

- QR smoke scope was expanded from one generic placeholder into two explicit business QR types:
  - `common`
  - `megapolis`
- The project can now generate QR PNG assets directly from template URLs and business parameters.
- New QR-related config inputs:
  - `CLIENT_BIN`
  - `QR_SOURCE_URL`
  - `QR_SOURCE_PAYLOAD`
  - `QR_GENERATED_IMAGE_PATH`
  - `QR_AMOUNT`
  - `QR_INVOICE_ID`
  - `QR_INVOICE_TITLE`
  - `QR_MEGAPOLIS_CONTRACT`
  - `QR_COMMON_TEMPLATE`
  - `QR_MEGAPOLIS_TEMPLATE`
- Current implementation status:
  - QR asset generation is ready
  - smoke suite is structured for both QR types
  - live native QR scanner/gallery locators still need one emulator pass before the test can go green end-to-end

## Update On 2026-04-18 (QR Flow Implemented Locally)

- The QR smoke flow is now implemented as a real local Appium flow, not a placeholder skip.
- Current automated path:
  - enter `OnlineDuken`
  - switch to native `QR` tab
  - open the native gallery button
  - select the first image from Android Photo Picker
  - wait for the native payment screen
  - tap `Оплатить`
- New native page objects and flow helpers were added for:
  - native `QR` scanner
  - Android Photo Picker
  - native payment screen
- Live backend result with a dummy `CLIENT_BIN`:
  - toast: `Неправильный ИИН/БИН клиента в QR`
- Practical implication:
  - the automation path itself is now proven
  - the remaining blocker for a green QR smoke is a real client BIN for the test user
- Key artifacts:
  - `artifacts/qr_probe_after_photo_select_native.png`
  - `artifacts/qr_probe_after_pay_click_generic_3s.png`
  - `artifacts/qr_payment_invalid_bin_toast.png`

## Update On 2026-04-18 (Local Parallel Attempt)

- Local true parallel execution was moved from design-only into real machine setup:
  - second local AVD clone created: `Medium_Phone_Parallel`
  - second emulator brought up on `emulator-5556`
  - second Appium server brought up on `http://127.0.0.1:4725`
- The framework now supports real worker-to-device mapping through:
  - `LOCAL_ANDROID_DEVICE_MATRIX`
- Smoke fixtures were updated so parallel workers use isolated mobile sessions rather than accidentally constructing shared session fixtures.
- Additional WebView recovery logic was added:
  - route fallback for `catalog`, `orders`, `bonuses`
  - `WEBVIEW` reconnection attempt when chromedriver loses DevTools connection
- Current honest state:
  - local two-device infrastructure is up
  - short validation showed the setup is close, but long local parallel runs are still unstable/slow on this host
  - BrowserStack remains the recommended path for routine parallel smoke in CI

## Update On 2026-04-18 (CI Toggle Refined)

- `smoke.yml` now supports a temporary push-smoke disable switch:
  - repository variable `ENABLE_PUSH_SMOKE=false`
- `workflow_dispatch` can still force a smoke run even while push smoke is disabled.
- Push smoke is now prepared for BrowserStack parallel execution with:
  - `ONLINEDUKEN_ENTRY_MODE=token`
  - `pytest -n 2`
- `manual.yml` remains the intended path for manual/regression execution.

## Update On 2026-04-18 (Automatic Local Bootstrap Added)

- Added a one-command local launcher:
  - `scripts/run_local_smoke.ps1`
- The launcher now prepares the local Android/Appium stack automatically:
  - ensures Python dependencies are installed
  - ensures global Appium is installed
  - ensures the Appium `uiautomator2` driver is installed
  - starts `adb`
  - starts the Android emulator if needed
  - starts fresh Appium server processes on the required ports
  - exports the local env vars required for the project
- Verified result:
  - bootstrap mode now completes successfully
  - local checks after bootstrap confirmed:
    - `adb devices` shows `emulator-5554`
    - `http://127.0.0.1:4723/status` returns ready
- A focused token-mode validation also passed:
  - `test_smoke_onlineduken_entry`
  - `test_smoke_catalog_has_suppliers`
- The original local startup error:
  - `Could not find a connected Android device in 20000ms`
  is now addressed by the launcher/bootstrap layer rather than left to raw pytest/Appium startup.
- Current remaining blocker for long local smoke runs:
  - the emulator intermittently hangs on `adb` commands such as `shell ps -A`, `force-stop`, and hidden-api cleanup
  - when that happens, Appium can lose the `WEBVIEW` context and later die during session cleanup
  - this is currently an emulator/adb stability problem, not a missing dependency/bootstrap problem
- Local safe-smoke strategy was re-stabilized:
  - local sequential smoke again prefers a shared Appium session
  - isolated sessions remain for BrowserStack and `xdist` workers

## Update On 2026-04-19 (QR Smoke Green, Full Smoke Rechecked)

- User provided a real client BIN for QR testing:
  - `900423400509`
- QR smoke was updated and revalidated against the live native payment flow.
- Important native finding:
  - after QR upload, the payment screen for this path is `Подписание платежа`
  - the primary action is effectively a signing step, not only a plain `Оплатить`
- Result:
  - `test_smoke_qr_payment_flow[qr-common]` -> passed
  - `test_smoke_qr_payment_flow[qr-megapolis]` -> passed
- The full local smoke suite was then rerun in token mode with the same BIN.
- To avoid one broken Appium/WebView session poisoning the whole suite, smoke fixtures were switched back to isolated per-test sessions for this run.
- Latest full smoke result:
  - `5 passed`
  - `2 failed`
  - `1 skipped`
- Passed:
  - `test_smoke_onlineduken_entry`
  - `test_smoke_orders_navigation`
  - `test_smoke_bonuses_navigation_and_history`
  - `test_smoke_qr_payment_flow[qr-common]`
  - `test_smoke_qr_payment_flow[qr-megapolis]`
- Failed:
  - `test_smoke_catalog_has_suppliers`
  - `test_smoke_cart_and_order_creation`
- Skipped:
  - `test_smoke_invoice_payment_from_home`
  - skip reason: missing `INVOICE_REFERENCE`
- Current red area is now concentrated in catalog-dependent WebView checks rather than in QR or auth flows.
- A dedicated run report was added:
  - `SMOKE_RUN_REPORT_2026-04-19.md`

## Update On 2026-04-19 (Shared Session Smoke Refactor)

- Smoke execution strategy was refactored to reduce repeated full logins.
- The suite is now split conceptually into:
  - isolated `auth smoke`
  - shared-session `UI smoke`
  - separate shared-session `payments smoke`
- New behavior:
  - UI checks reuse one long-lived Appium session and try to recover back to `OnlineDuken` home between tests
  - payment checks reuse a different long-lived Appium session so state-changing flows do not contaminate UI navigation checks
  - if a shared session becomes unhealthy, the managed session layer can restart only that session instead of poisoning the rest of the chain
- QR generation was tightened:
  - QR payloads now use unique numeric values per run

## Update On 2026-04-27 (BrowserStack Stability Pass)

- A fresh project audit was performed against the current BrowserStack and pytest/Appium strategy.
- BrowserStack-safe smoke remains the primary cloud path until a build with explicit `OnlineDuken` WebView debugging is available.
- The BrowserStack-safe path now intentionally uses full mobile login for every cloud test session:
  - `ONLINEDUKEN_ENTRY_MODE=full`
  - `B2B_SHARED_AUTH_BOOTSTRAP=false`
  - `BROWSERSTACK_WEBVIEW_ENABLED=false`
  - `pytest -m "smoke and browserstack_safe and not manual" -n 3`
- A dedicated local BrowserStack demo launcher was added:
  - `scripts/run_browserstack_smoke.ps1`
- CI smoke was updated to:
  - run BrowserStack-safe smoke with three xdist workers
  - upload raw `allure-results` as a GitHub Actions artifact
  - keep the `ENABLE_PUSH_SMOKE=false` kill switch
- Healthcheck was tightened:
  - plain URLs now require `2xx/3xx`
  - exact expected statuses can be configured with `URL|200` or `URL|200,204`
  - `404` is no longer treated as an available environment by default
- Auth bootstrap was tightened:
  - cached/shared auth URLs must be real `/web/customer-frontend/auth?ob-auth-token=...` URLs
  - generic `customer-frontend` routes are rejected to avoid false authenticated states
- BrowserStack driver creation was cleaned up:
  - credentials are now passed through Selenium/Appium client config instead of embedding them in the hub URL
  - BrowserStack Appium/device logs are explicitly enabled in capabilities
  - pytest now marks BrowserStack sessions as passed/failed through `browserstack_executor`
- A root-level `browserstack.yml` was added as an optional SDK migration layer.
- Current decision on BrowserStack SDK:
  - keep direct Appium + pytest as the stable primary path for now
  - use `browserstack.yml` later if the team wants SDK-managed reporting, app upload, or Test Observability
  - do not migrate immediately while BrowserStack-safe mobile login stability is the main priority
- Real BrowserStack verification after the stability pass:
  - build name: `audit-browserstack-full-login-20260427-clean`
  - build hashed id: `500d123b47e61f7e863d8258c7dbc53199a0529b`
  - command: `scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure`
  - result: `2 passed`
  - runtime: `128.16s`
  - local `allure-results` was cleaned before the final successful run
- Important BrowserStack finding:
  - fully simultaneous logins with the same test phone can invalidate/expire the OTP flow in another worker
  - the framework now staggers BrowserStack full-login starts with `BROWSERSTACK_LOGIN_STAGGER_SEC`
  - if the smoke set grows beyond two safe tests, the best long-term improvement is a pool of independent test users, one per worker

## Update On 2026-05-04 (BrowserStack QR And WebView UI Smoke Green)

- BrowserStack QR smoke was enabled and validated for both configured QR templates:
  - `common`
  - `megapolis`
- The QR flow now works in BrowserStack through:
  - generated QR PNG assets
  - Appium `push_file` into `/sdcard/Pictures`
  - Android media scan where available
  - native Android Photo Picker selection
- BrowserStack Android Photo Picker locators were updated for:
  - package `com.google.android.providers.media.module`
  - clickable `Photo taken...` grid items
- Main BrowserStack-safe smoke result:
  - build name: `smoke-browserstack-main-qr-ui-20260504`
  - build id: `2e3a2b470f344595f0aacc49844cdf915f33eee1`
  - result: `4 passed`
  - tests: app shell, OnlineDuken native container, QR common, QR megapolis
- BrowserStack WebView UI subset was also validated successfully with `BROWSERSTACK_WEBVIEW_ENABLED=true`:
  - build name: `ui-webview-browserstack-20260504`
  - build id: `0910889a101cda30abbd0121975074b931da391a`
  - result: `4 passed`
  - tests: OnlineDuken entry, catalog, orders, bonuses/history
- Detailed report:
  - `BROWSERSTACK_RUN_REPORT_2026-05-04.md`
  - this prevents the main happy-path QR smoke from accidentally reusing an older QR and falling into the business flow for re-signing a pending payment
- Live verification after the refactor:
  - `test_smoke_onlineduken_entry`
  - `test_smoke_orders_navigation`
  - `test_smoke_bonuses_navigation_and_history`
  - `test_smoke_qr_payment_flow[qr-common]`
  - `test_smoke_qr_payment_flow[qr-megapolis]`
  - result: `5 passed`

## Update On 2026-06-10 (Refactor Branch Verification And Login Lock)

- The refactor branch `claude/laughing-mahavira-3d2680` went through real verification before merge:
  - unit tests: `49 passed` (then `54 passed` after the login-lock tests were added)
  - full collection: `71 tests`, no import errors after the flows/tests split
  - the previously uploaded BrowserStack app had expired (30-day retention), so the APK was re-uploaded:
    - new app id: `bs://628110de9fb881fa60d22391aa793a7c745de327`
    - stable custom id: `onlineduken-stage`
- A real branch bug was found and fixed:
  - both local launchers and the README still installed from the deleted `requirements-ci.txt`
  - they now use `pip install -e .[ci]`
- BrowserStack-safe main + QR pack on the branch:
  - first run with the old 20s stagger failed on the known OTP race (`auth code expired after sms entry`), `2 passed / 1 failed`
  - the same failed test passed solo (`1 passed in 83s`), proving the login flow itself is healthy on the branch
  - rerun with `BROWSERSTACK_LOGIN_STAGGER_SEC=60`: `4 passed in 257s` (build `refactor-verify-main-qr-stagger60-20260610`)
- WebView UI subset run hit the same OTP race from the other side:
  - a worker retry re-requested SMS while staggered workers were starting, `2 passed / 1 error`
  - conclusion: the stagger only lowers collision probability; retries still collide
- Structural fix implemented: cross-process login lock
  - new `mobile_automation/login_lock.py` (filelock-based) serializes the whole phone/SMS/PIN retry loop across workers
  - `try_complete_login` now runs under the lock, so all entry points are covered
  - waiting workers ping their Appium session so BrowserStack does not kill idle sessions (~90s limit)
  - new env knobs: `LOGIN_LOCK_ENABLED` (default true), `LOGIN_LOCK_TIMEOUT_SEC` (600), `LOGIN_LOCK_PATH`
  - covered by 5 unit tests
- Login stagger raised 20 -> 60 in config default and both workflows; with the lock in place it is now a secondary safety net and can be lowered after the next validated cloud run
- Development workflow agreed with the user:
  - new WebView tests are developed first in the desktop-browser web suite, then validated once on the local emulator, and only then on BrowserStack before push
- Still pending before merge:
  - one green WebView UI subset run on BrowserStack with the login lock active (cloud runs are paused at user request)
  - long-term: a pool of independent test users, one per worker, remains the proper fix for shared-phone OTP contention

## Update On 2026-06-10 (Three-Tier Execution Scheme)

- The execution strategy was restructured into three tiers, agreed with the user:
  - web suite in a plain browser with an injected auth token -> frontend-only checks, the main development loop, and push CI
  - local emulator (Appium hybrid) -> business-logic flows: payments, QR, native screens, context switching
  - BrowserStack -> cross-platform device checks only, manual runs only
- Implementation:
  - new launcher `scripts/run_web_suite.ps1` (-Headless, -Allure, -Workers, -KExpression, -SkipInstall); forces `TARGET=local` so mobile/cloud env values cannot leak into a web run
  - `smoke.yml` renamed to `web-smoke` semantics: push now runs `pytest -m web -n 2` in headless Chrome on the runner instead of BrowserStack App Automate
  - the `ENABLE_PUSH_SMOKE` kill switch and the healthcheck gate are unchanged
  - `manual.yml` (mobile-manual) remains the BrowserStack entry point with platform choice and marker expression
  - README documents the tiers and the practical rule for where a new test starts
- Verified locally:
  - launcher run without auth -> `5 skipped, 71 deselected`, clean skip reason about the missing auth URL/token
- What the push web smoke still needs to turn from skip to green in CI:
  - either `B2B_OB_AUTH_TOKEN` / `B2B_AUTH_URL` secrets (tokens expire, so this is the weaker option)
  - or the internal login endpoint secrets (`B2B_INTERNAL_LOGIN_URL` / `B2B_INTERNAL_CLIENT_ID` / `B2B_INTERNAL_CLIENT_SECRET`) for self-refreshing auth
  - plus `TEST_ENV_HEALTHCHECK_URLS` so the healthcheck gate reflects the real web env
