# BrowserStack Smoke Report - 2026-05-04

## Summary

Two BrowserStack smoke runs were completed successfully against project `B2B Mobile Demo`.

The run used:

- Android app: `bs://c275dbb0208fb6c0f990a5433bf793fe9f5329dc`
- Device: `Samsung Galaxy S24`
- OS: `Android 14.0`
- Client BIN: `900423400509`
- Login mode: full mobile login
- Parallel workers: `3`

## Main + QR Smoke

Build name: `smoke-browserstack-main-qr-ui-20260504`

Build hashed id: `2e3a2b470f344595f0aacc49844cdf915f33eee1`

Public build URL: `https://app-automate.browserstack.com/dashboard/v2/public-build/aGVWN1I2cGFmZGVhaStXWlhXTDBta0JoY25hSFpYL3orYjdKbnpVN2lzVXRZdUhHVlU2ZEI3ZGs4dm5NTzIxV082bzdyaTVsNW5MQXhINVVrb050NkE9PS0tcTZrWUlOVFNEN1Jnb1FHU01Ub1p2dz09--64d50e9532c12fc6a5b84236e113a0377515a88c`

Command:

```powershell
$env:BROWSERSTACK_APP_ANDROID='bs://c275dbb0208fb6c0f990a5433bf793fe9f5329dc'
$env:CLIENT_BIN='900423400509'
powershell -ExecutionPolicy Bypass -File .\scripts\run_browserstack_smoke.ps1 -Workers 3 -Allure -BuildName smoke-browserstack-main-qr-ui-20260504
```

Result:

- `4 passed`
- runtime: `275.96s`
- BrowserStack build status: `done`

Passed sessions:

- `test_smoke_app_shell_is_reachable`
  - session id: `26ad721e748b38f868c6c2fe02a7f4a753277d0e`
  - duration: `79s`
- `test_smoke_onlineduken_native_container_entry`
  - session id: `948ce86ddaf32bc4c1fa6ad43c08616513e7dab9`
  - duration: `98s`
- `test_smoke_qr_payment_flow[qr-common]`
  - session id: `1db5b4908bb702a7f84dc45fa55976b4116bff0e`
  - duration: `172s`
- `test_smoke_qr_payment_flow[qr-megapolis]`
  - session id: `ab92ccc157ec0bd3fd50655e99c180412f19fae8`
  - duration: `190s`

## WebView UI Smoke

Build name: `ui-webview-browserstack-20260504`

Build hashed id: `0910889a101cda30abbd0121975074b931da391a`

Public build URL: `https://app-automate.browserstack.com/dashboard/v2/public-build/NklMOThWTWoxU1JCU3ZISGlxYzFuV1lQcTNyUms2TTlDZ1pZeEo1cGFFR2N4WGVzbElWQjlSS2Z4ZG9ReE43QXVnYllaMkgrTEMxNm8vdVQ1YlhSbHc9PS0tWEovczBaZlFoaTBocnpjTVBqb0FtUT09--8ba694962c57ffcddbbfb1d6902f0d6ecb3e0dd4`

Command:

```powershell
$env:TARGET='browserstack'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='full'
$env:BROWSERSTACK_WEBVIEW_ENABLED='true'
$env:BROWSERSTACK_APP_ANDROID='bs://c275dbb0208fb6c0f990a5433bf793fe9f5329dc'
$env:BROWSERSTACK_BUILD_NAME='ui-webview-browserstack-20260504'
$env:CLIENT_BIN='900423400509'
py -3.12 -m pytest tests\smoke\test_smoke_suite.py -k "onlineduken_entry or catalog_has_suppliers or orders_navigation or bonuses_navigation" -n 3 --alluredir=allure-results-ui -q -ra --maxfail=1
```

Result:

- `4 passed`
- runtime: `251.47s`
- BrowserStack build status: `done`

Passed sessions:

- `test_smoke_onlineduken_entry`
  - session id: `3e5c6c6c474b2ce75d396792f42b499717315ad1`
  - duration: `88s`
- `test_smoke_catalog_has_suppliers`
  - session id: `f5ce774567cca7e03ec80117682ac25e9d72dbbd`
  - duration: `122s`
- `test_smoke_orders_navigation`
  - session id: `df19f3f42aa054e7657ed72cd449060ff5191e5c`
  - duration: `248s`
- `test_smoke_bonuses_navigation_and_history`
  - session id: `1260b9bc51b63acb143eca67ca518b889aeb7169`
  - duration: `140s`

## Notes

- QR smoke now runs in BrowserStack by pushing the generated QR PNG into the device gallery and selecting it through the native Android photo picker.
- Android Photo Picker on BrowserStack uses package `com.google.android.providers.media.module`; locators were updated for that package.
- WebView UI smoke was re-enabled for the verified subset by setting `BROWSERSTACK_WEBVIEW_ENABLED=true`.
