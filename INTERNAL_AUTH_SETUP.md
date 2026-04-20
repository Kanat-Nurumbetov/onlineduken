# Internal Auth Setup

## Purpose

This file captures the current bootstrap strategy for parallel `OnlineDuken` smoke runs.

## Current Bootstrap Order

When `ONLINEDUKEN_ENTRY_MODE=token`, the shared auth URL is resolved in this order:

1. internal login endpoint
2. `B2B_AUTH_FETCH_COMMAND`
3. one bootstrap login through the mobile app with token extraction from `WebView`
4. cached runtime auth URL

The resolved auth URL is cached in:
- `artifacts/runtime/b2b_auth.json`

It is then passed into all `pytest-xdist` workers before test execution.

## Internal Endpoint Shape

Expected request:
- `POST`
- URL pattern:
  - `https://testapi.onlinebank.kz/internal/internal/users/login-user-by-id-and-contract/<user_id>/<contract_id>?loggedInBy=sms`
- form fields:
  - `client_id`
  - `client_secret`
  - `grant_type=internal`

Expected response handling:
- ready auth URL -> use directly
- `ob_auth_token` -> convert into `B2B_AUTH_URL`
- `token` -> convert into `B2B_AUTH_URL`
- `access_token` -> convert into `B2B_AUTH_URL`

## Local Secrets Rule

Do not commit real values for:
- `B2B_INTERNAL_CLIENT_ID`
- `B2B_INTERNAL_CLIENT_SECRET`
- `BROWSERSTACK_USERNAME`
- `BROWSERSTACK_ACCESS_KEY`
- `BROWSERSTACK_APP_ANDROID`
- live auth tokens or auth URLs

Recommended local file:
- `.env.local`
or
- `.env.parallel.local`

Use `.env.internal.example` as the starting template.

## Current Known Test Data

- phone: `7772229999`
- PIN: `0000`
- contract suffix: `376`
- SMS: any numeric code in the current test environment

## Important Limitation

The app-login fallback is implemented, but the exact reusable token location inside `WebView` still needs live validation against the current stage build. If no reusable token is found in `current_url`, `document.cookie`, `localStorage`, or `sessionStorage`, the bootstrap falls through without producing a shared auth URL.
