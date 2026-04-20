# Smoke Run Report 2026-04-19

## Context

- Target: `local`
- Platform: `android`
- Entry mode: `token`
- Client BIN for QR: `900423400509`

## Commands Used

QR-only smoke:

```powershell
$env:TARGET='local'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:CLIENT_BIN='900423400509'
py -3.12 -m pytest tests\smoke\test_smoke_suite.py -k "qr_payment_flow" -q -s -ra
```

Full smoke:

```powershell
$env:TARGET='local'
$env:PLATFORM='android'
$env:ONLINEDUKEN_ENTRY_MODE='token'
$env:CLIENT_BIN='900423400509'
py -3.12 -m pytest -m smoke -q -s -ra
```

## QR Smoke Result

- `test_smoke_qr_payment_flow[qr-common]` -> `PASSED`
- `test_smoke_qr_payment_flow[qr-megapolis]` -> `PASSED`

Notes:
- The valid `CLIENT_BIN` is now accepted by backend validation.
- The QR payment screen for this flow is actually `Подписание платежа`.
- The correct primary action is `Подписать`, not only `Оплатить`.
- The smoke assertion is now satisfied when the payment proceeds to the confirmation stage after the signing action.

## Full Smoke Result

Summary:
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
  - reason: `INVOICE_REFERENCE is not configured yet.`

## Current Failure Analysis

### Catalog

`test_smoke_catalog_has_suppliers` currently fails because the WebView reaches the catalog route but the expected DOM markers are not found consistently:
- no `div.distributor-card`
- no `div.search-centered`
- no `hb2b-distributor` root marker in the captured DOM snapshot

This looks like a locator / route-shape mismatch on the live catalog page, not a login or QR blocker.

### Cart / Order Creation

`test_smoke_cart_and_order_creation` currently fails for the same catalog-entry reason:
- the flow cannot reliably find the catalog tab DOM target
- direct route fallback opens the route, but `CatalogPage.TITLE` still does not stabilize

This is currently blocked by catalog DOM stabilization rather than by cart business logic itself.

## Useful Outcome

- QR smoke is now green for both requested QR types.
- Full smoke is stable enough to produce a reproducible status split.
- The remaining red area is concentrated in catalog-dependent flows.
