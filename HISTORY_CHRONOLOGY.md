# History And Chronology

## User Requests In Chronological Order

1. User asked whether the APK could be analyzed for future E2E tests based on their test cases.
2. User provided APK path:
   - `C:\Users\Kanat\Downloads\halyk_bank_app.apk`
3. User asked to confirm the APK could be opened.
4. User asked to show the screen at app startup.
5. User asked to shut down the emulator to reduce computer load.
6. User resumed and provided test user:
   - phone `7772229999`
   - PIN `0000`
7. User explained that:
   - the account has many contracts;
   - contract ending with `376` should be chosen from the top-left selector;
   - from the main screen we should open `OnlineDuken`;
   - it redirects to the app that should be covered by tests;
   - requested general exploration of screens and locator collection;
   - suggested using `Page Object Model`;
   - noted there are many `WebView` pages plus native pages.
8. During investigation, a server error was found and the user asked to pause because test environment maintenance was likely in progress.
9. User later said the test environment was working again.
10. User уточнил, that any numeric SMS code can be used.
11. User asked to create smoke tests for important functionality, especially payments.
12. User asked how to continue the chat from another device in the browser.
13. User clarified that the chat was not visible in the browser and asked how to transfer context and progress.
14. User asked to prepare all possible handoff files:
   - history of work;
   - user requests in chronological order;
   - what was already defined and found;
   - everything useful for continuation.

## What Was Done In Chronological Order

### APK validation

- Confirmed the APK file exists and is readable.
- Opened archive structure and confirmed:
  - `AndroidManifest.xml`
  - `resources.arsc`
  - `classes.dex`

### First startup capture

- Started Android emulator.
- Installed APK.
- Determined launch activity.
- Captured startup / login screen screenshot:
  - `halyk_start_screen.png`

### Initial pause

- Emulator and related processes were shut down after the user asked to reduce system load.

### First deep login investigation

- Restarted emulator.
- Cleared app state.
- Opened login flow.
- Collected native UI dump for login screen.
- Tried login with provided phone number.
- Received server error dialog:
  - `Attention!`
  - `Неизвестная ошибка сервера`
- Captured logcat and found the real backend issue:
  - `GET https://testapi.onlinebank.kz/authentication/get-sms/7772229999?app=android`
  - response `503`

### Static APK investigation while backend was failing

- Extracted app metadata with `aapt`.
- Searched APK strings and resources for:
  - `OnlineDuken`
  - `onlineduken`
  - `webview`
  - `contract`
- Found:
  - `go_to_onlineduken`
  - `onlineduken_banner_*`
  - `kz.halyk.onlinebank.stage:id/webview`
  - `kz.halyk.onlinebank.stage:id/contractSelector`
  - `kz.halyk.onlinebank.stage:id/select_contract_container`
  - layout names such as `fragment_webview`
- Found `B2BActivity` in manifest:
  - `kz.halyk.onlinebank.ui_release4.screens.b2b.activity.B2BActivity`
- Found deep link support for:
  - `/applink/b2b/`
  - `/appLink/b2b/`

### Successful login investigation after backend recovery

- Re-launched emulator.
- Cleared app data again for a clean run.
- Repeated login flow.
- Reached SMS confirmation screen successfully.
- Confirmed any numeric code can be entered.
- Entered `123456`.
- Reached passcode creation flow.
- Entered PIN `0000`, then confirmed it again.

### Main app onboarding / permissions investigation

- After login, several native/system steps were observed:
  - notifications permission
  - camera/video identification dialog
  - internal security onboarding
  - location permission
  - contacts permission
  - nearby devices / Bluetooth-style permission chain
- Some of these screens were collected as screenshots and XML dumps.

### Discovery of separate B2B package

- Found installed package:
  - `com.example.b2b`
- Opened it directly.
- Determined it was just a placeholder screen:
  - `Hello Android!`
- Marked it as not the real target for E2E.

### Reliable OnlineDuken entry via deep link

- Opened deep link:
  - `https://halyk.onlinebank.kz/appLink/b2b/`
- App routed to passcode unlock screen.
- Entered PIN `0000`.
- App opened:
  - `kz.halyk.onlinebank.ui_release4.screens.b2b.activity.B2BActivity`
- Confirmed B2B shell contains WebView:
  - `kz.halyk.onlinebank.stage:id/webview`

### OnlineDuken WebView inspection

- Enabled WebView inspection by forwarding DevTools socket.
- Confirmed active page:
  - title: `Onlinebank - B2B Market`
  - URL: `https://b2b.test.onlinebank.kz/web/customer-frontend/`
- Collected DOM summaries for major routes:
  - home
  - catalog
  - orders
  - bonuses
  - payment
  - cart
  - more
- Saved JSON route summary:
  - `artifacts\b2b_route_summaries.json`
- Saved screenshots for these routes:
  - `artifacts\b2b_screens\*.png`

### Smoke test planning

- Drafted initial smoke flows with payments as highest priority:
  - QR payment
  - invoice payment from home
  - cart and order creation
  - OnlineDuken login entry
  - supplier visibility in catalog
  - orders navigation
  - bonuses and bonus history

## Things Confirmed

- APK is valid.
- Login native screens are accessible.
- SMS step can be passed with arbitrary digits.
- PIN can be set to `0000`.
- `OnlineDuken` is not a pure separate app for this flow.
- Real target is a WebView inside `B2BActivity`.
- Major customer routes inside `OnlineDuken` were identified.

## Things Not Fully Confirmed Yet

- Exact contract selection step for contract ending with `376`.
- Full end-to-end navigation from the main dashboard to `OnlineDuken` using only production-like taps.
- Full deep business flows:
  - create order
  - cashier flow
  - QR payment completion
  - invoice payment completion

## Most Important Technical Conclusion

For test automation, the project should be treated as a hybrid app:
- native Android shell for auth and app wrappers;
- WebView-based business UI for `OnlineDuken`.

## Update On 2026-04-16

- User provided an internal `POST` endpoint for authorization and token retrieval.
- The automation project was extended to support shared token bootstrap through:
  - internal login endpoint
  - command-based token fetch
  - fallback bootstrap login through the mobile app
  - runtime cache
- New context files were added to preserve this state:
  - `INTERNAL_AUTH_SETUP.md`
  - `.env.internal.example`

## Update On 2026-04-18

- User provided two QR URL formats to include into smoke coverage:
  - common QR
  - Megapolis QR
- The project was updated to support QR template-driven PNG generation and separate QR smoke cases for both formats.
- QR smoke was then converted from placeholder into a real native flow:
  - QR tab
  - gallery upload
  - payment screen
  - `Оплатить`
- Live backend feedback showed the remaining business blocker:
  - dummy BIN leads to toast `Неправильный ИИН/БИН клиента в QR`
- Local parallel work also moved forward:
  - second AVD clone created
  - second emulator/Appium slot brought up
  - worker/device mapping added through `LOCAL_ANDROID_DEVICE_MATRIX`
- CI behavior was refined:
  - push smoke can now be disabled temporarily with repository variable `ENABLE_PUSH_SMOKE=false`
  - manual workflow remains the intended regression entry point

## Update On 2026-04-20

- User confirmed a better smoke strategy:
  - keep one isolated auth smoke
  - keep one shared-session UI smoke
  - keep one shared-session payments smoke
- Project was adapted so repeated full login is no longer required for every smoke test.
- User then clarified the expected catalog/cart behavior:
  - catalog smoke is valid if the page opens, whether suppliers exist or the page shows a reasonable empty state
  - cart flows should cover both:
    - catalog -> product -> cart -> create order
    - home product -> cart -> create order
- Live probes showed that current supplier data is not deterministic enough for reliable cart smoke yet.
- Temporary decision taken together with the user:
  - keep cart smoke in the suite
  - mark both cart tests as explicit `skip`
  - wait for a stable supplier prepared specifically for automation
