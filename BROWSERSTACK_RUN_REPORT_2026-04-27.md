# BrowserStack Safe Smoke Report - 2026-04-27

Build name: `audit-browserstack-full-login-20260427-clean`

Build hashed id: `500d123b47e61f7e863d8258c7dbc53199a0529b`

Public build URL: `https://app-automate.browserstack.com/dashboard/v2/public-build/SU5NaE9XTDMvbGpxdUFyakFOcXRDaGN0SzZrdFFGejE4KzhwUjZRWE9uY2FmVlhIZnJGSE1Udm44ZGxkU21lR0hDL0RHSnFzeFZ0YU9Od0tqdTZhQ1E9PS0tNWxXMlpacTFLV09lbXp1a1VDazI4QT09--2a0a6f8f9e32ff1ce768282f25f590ea10dd51a7`

Command:

```powershell
$env:BROWSERSTACK_APP_ANDROID='bs://c275dbb0208fb6c0f990a5433bf793fe9f5329dc'
powershell -ExecutionPolicy Bypass -File .\scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure -BuildName audit-browserstack-full-login-20260427-clean
```

Effective scope:

- `TARGET=browserstack`
- `PLATFORM=android`
- `ONLINEDUKEN_ENTRY_MODE=full`
- `B2B_SHARED_AUTH_BOOTSTRAP=false`
- `BROWSERSTACK_WEBVIEW_ENABLED=false`
- `BROWSERSTACK_LOGIN_STAGGER_SEC=20`
- marker expression: `smoke and browserstack_safe and not manual`
- xdist workers: `3`

Result:

- `2 passed`
- runtime: `128.16s`
- BrowserStack build status: `done`

Sessions:

- `test_smoke_onlineduken_native_container_entry`
  - session id: `9bf78641448e7cc7b457535e2c0d0ebfa2c7735b`
  - device: `Samsung Galaxy S24`
  - OS: `Android 14.0`
  - status: `passed`
  - duration: `105s`
- `test_smoke_app_shell_is_reachable`
  - session id: `45a7fbcecfeda5cde1cabeaa42f0d8c2b1dc4893`
  - device: `Samsung Galaxy S24`
  - OS: `Android 14.0`
  - status: `passed`
  - duration: `84s`

Finding:

- Fully simultaneous full logins with one shared test phone can invalidate OTP for another worker.
- `BROWSERSTACK_LOGIN_STAGGER_SEC=20` now staggers cloud full-login starts by xdist worker index.
- If the BrowserStack-safe suite grows beyond the current two tests, the preferred long-term solution is a pool of independent test users, one per worker.
