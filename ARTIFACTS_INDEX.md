# Artifacts Index

## Main Artifacts Folder

- `C:\Users\Kanat\Documents\New project\artifacts`

## High-Value Files

### APK metadata

- `C:\Users\Kanat\Documents\New project\artifacts\aapt_badging.txt`
  - package/version/permissions metadata from APK

### Login and auth flow

- `C:\Users\Kanat\Documents\New project\artifacts\auth.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\auth.png`
- `C:\Users\Kanat\Documents\New project\artifacts\sms_or_error.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\sms_or_error.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_sms.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_sms.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_first.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_first.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_confirm.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_confirm.png`
- `C:\Users\Kanat\Documents\New project\artifacts\app_link_b2b.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\app_link_b2b.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_deeplink.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_pin_deeplink.png`

### Errors and logs

- `C:\Users\Kanat\Documents\New project\artifacts\after_login_tap.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_login_tap.png`
- `C:\Users\Kanat\Documents\New project\artifacts\login_logcat.txt`
  - contains the earlier `503` backend evidence

### Permission / onboarding flow

- `C:\Users\Kanat\Documents\New project\artifacts\home_or_next.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\home_or_next.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_camera_dialog_cancel.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_camera_dialog_cancel.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_location_next.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_location_next.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_location_allow.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_location_allow.png`
- `C:\Users\Kanat\Documents\New project\artifacts\after_contacts_decision.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\after_contacts_decision.png`
- `C:\Users\Kanat\Documents\New project\artifacts\permission_chain_current.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\permission_chain_current.png`
- `C:\Users\Kanat\Documents\New project\artifacts\main_after_grants.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\main_after_grants.png`
- `C:\Users\Kanat\Documents\New project\artifacts\post_onboarding.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\post_onboarding.png`

### B2B / OnlineDuken routing and screen research

- `C:\Users\Kanat\Documents\New project\artifacts\b2b_route_summaries.json`
  - DOM summaries for multiple `OnlineDuken` routes
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_main.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_main.png`
  - placeholder `com.example.b2b` app
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_activity.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_activity.png`

### Latest local smoke stabilization probes

- `C:\Users\Kanat\Documents\New project\artifacts\web_store_popup_detected.html`
- `C:\Users\Kanat\Documents\New project\artifacts\web_store_popup_detected.png`
  - captured the visible `WebView` store-selection popup before automatic selection
- `C:\Users\Kanat\Documents\New project\artifacts\webview_after_onlineduken_entry.html`
- `C:\Users\Kanat\Documents\New project\artifacts\webview_after_onlineduken_entry.png`
  - captured the `OnlineDuken` home state after entry stabilization
- `C:\Users\Kanat\Documents\New project\artifacts\bonuses_page_probe.html`
- `C:\Users\Kanat\Documents\New project\artifacts\bonuses_page_probe.png`
  - confirms the current bonus history card DOM shape
- `C:\Users\Kanat\Documents\New project\artifacts\catalog_page_probe.html`
- `C:\Users\Kanat\Documents\New project\artifacts\catalog_page_probe.png`
  - confirms the current catalog route and supplier card DOM

### OnlineDuken screenshots by route

Folder:
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens`

Files:
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\home.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\catalog.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\orders.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\bonuses.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\payment.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\cart.png`
- `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\more.png`

## Top Files To Read First

If another agent or browser session needs the fastest re-entry, start with:

1. `C:\Users\Kanat\Documents\New project\HANDOFF_ONLINEDUKEN.md`
2. `C:\Users\Kanat\Documents\New project\HISTORY_CHRONOLOGY.md`
3. `C:\Users\Kanat\Documents\New project\TEST_CASES_SMOKE_DRAFT.md`
4. `C:\Users\Kanat\Documents\New project\artifacts\b2b_route_summaries.json`

## Most Important Screenshots

If only a few screenshots are needed:

- Startup/login:
  - `C:\Users\Kanat\Documents\New project\halyk_start_screen.png`
- SMS screen:
  - `C:\Users\Kanat\Documents\New project\artifacts\sms_or_error.png`
- PIN create:
  - `C:\Users\Kanat\Documents\New project\artifacts\after_sms.png`
- OnlineDuken home:
  - `C:\Users\Kanat\Documents\New project\artifacts\after_pin_deeplink.png`
- Store popup / stabilized home:
  - `C:\Users\Kanat\Documents\New project\artifacts\web_store_popup_detected.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\webview_after_onlineduken_entry.png`
- OnlineDuken route set:
  - `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\home.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\catalog.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\orders.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\bonuses.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\b2b_screens\payment.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\bonuses_page_probe.png`
  - `C:\Users\Kanat\Documents\New project\artifacts\catalog_page_probe.png`

## Notes

- XML files are useful for native Android locators.
- `b2b_route_summaries.json` is useful for WebView DOM and route-based POM design.
- `login_logcat.txt` is useful as evidence of the earlier stage backend incident.

## Update On 2026-04-18 (QR And Parallel Artifacts)

### QR flow artifacts

- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_tab_native.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_gallery_picker_native_path.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_photo_select_native.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_pay_click_generic_3s.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_pay_click_generic_8s.png`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_payment_invalid_bin_toast.png`
  - shows the current backend blocker for QR smoke with a dummy BIN

### Generated QR assets

- `C:\Users\Kanat\Documents\New project\artifacts\runtime\generated_qr_common.png`
- `C:\Users\Kanat\Documents\New project\artifacts\runtime\generated_qr_megapolis.png`

### Most useful QR debug files

- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_tab_native.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_gallery_picker_native_path.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_probe_after_photo_select_native.xml`
- `C:\Users\Kanat\Documents\New project\artifacts\qr_payment_invalid_bin_toast.xml`

## Update On 2026-04-22 (Successful BrowserStack Safe Smoke)

- `C:\Users\Kanat\Documents\New project\artifacts\browserstack\codex-browserstack-safe-20260422-run3\REPORT.md`
  - consolidated report for the successful parallel BrowserStack-safe run
  - includes build id, session ids, command, scope, and the fixes that made the run green

## Update On 2026-04-27 (BrowserStack Full-Login Safe Smoke)

- `C:\Users\Kanat\Documents\New project\artifacts\browserstack\audit-browserstack-full-login-20260427-staggered\REPORT.md`
  - consolidated report for the successful BrowserStack-safe run with full login
  - command used `scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure`
  - BrowserStack build id: `fabc5f2e7316efaffddd115804a95c63d666b437`
  - BrowserStack result: `2 passed`
  - includes the finding that same-user parallel OTP flows need worker login staggering
- `C:\Users\Kanat\Documents\New project\artifacts\browserstack\audit-browserstack-full-login-20260427-clean\REPORT.md`
  - latest clean rerun after adding automatic `allure-results` cleanup
  - BrowserStack build id: `500d123b47e61f7e863d8258c7dbc53199a0529b`
  - BrowserStack result: `2 passed`
  - local `allure-results` now contains only this last run

## Update On 2026-05-04 (BrowserStack QR And UI Smoke)

- `C:\Users\Kanat\Documents\New project\BROWSERSTACK_RUN_REPORT_2026-05-04.md`
  - consolidated tracked report for successful BrowserStack QR and UI smoke runs
  - main + QR build id: `2e3a2b470f344595f0aacc49844cdf915f33eee1`
  - main + QR result: `4 passed`
  - WebView UI build id: `0910889a101cda30abbd0121975074b931da391a`
  - WebView UI result: `4 passed`
- Local ignored Allure result folders from the run:
  - `allure-results`
  - `allure-results-ui`
