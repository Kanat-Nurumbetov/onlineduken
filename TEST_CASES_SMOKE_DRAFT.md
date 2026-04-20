# OnlineDuken Smoke Test Draft

## Priority Order

Business priority, highest first:

1. QR payment
2. Invoice payment from home
3. Cart fill and order creation
4. OnlineDuken entry
5. Supplier visibility in catalog
6. Orders page navigation
7. Bonuses page and bonus history

## Assumptions

- User logs in with:
  - phone `7772229999`
  - PIN `0000`
- SMS screen accepts any numeric code.
- `OnlineDuken` can be reached through the main app.
- Some test data for payments and QR images may still need to be provided by the user.

## Smoke Cases

### SMK-01 OnlineDuken entry

Priority:
- High

Objective:
- verify that the user can reach `OnlineDuken` from the application flow

Preconditions:
- app installed
- test environment available
- user credentials valid

Steps:
1. Open app.
2. Enter phone number.
3. Submit login.
4. Enter any numeric SMS code.
5. Enter PIN `0000` if passcode setup or unlock is required.
6. Navigate to `OnlineDuken`.

Expected result:
- user reaches `OnlineDuken` home page without critical error
- `B2BActivity` opens and WebView content loads

Automation notes:
- native + WebView hybrid case
- fallback technical entry found via `https://halyk.onlinebank.kz/appLink/b2b/`

### SMK-02 Suppliers are visible in Catalog

Priority:
- High

Objective:
- verify that supplier catalog is available and populated

Preconditions:
- user already in `OnlineDuken`

Steps:
1. Open `Каталог`.
2. Wait for suppliers list to load.
3. Check that at least one supplier card is visible.

Expected result:
- page title `Выберите поставщика` is shown
- supplier cards are visible
- action buttons like `Создать заказ` or supplier actions are visible

Automation notes:
- route observed: `/web/customer-frontend/distributors`
- useful selector candidates:
  - `h1.distributors__header-title`
  - `div.distributor-card`

### SMK-03 Orders navigation from home

Priority:
- Medium

Objective:
- verify navigation from home to orders page

Preconditions:
- user already in `OnlineDuken`

Steps:
1. On home page tap `Заказы` / `Мои заказы`.
2. Wait for orders page to load.

Expected result:
- orders page opens successfully
- page title `Мои заказы` is visible
- either list or empty state is shown without error

Automation notes:
- route observed: `/web/customer-frontend/orders`
- current UI text on home quick action appears as `Заказы`
- needs confirmation from business side whether user-facing wording should be `Мои заказы`

### SMK-04 Bonuses page and bonus history

Priority:
- Medium

Objective:
- verify bonuses page opens and history can be reached

Preconditions:
- user already in `OnlineDuken`

Steps:
1. On home page tap `Бонусы`.
2. Wait for bonuses page to load.
3. Open bonus history.

Expected result:
- bonuses page is displayed
- bonus metrics are visible
- history page or history list opens successfully

Automation notes:
- route observed: `/web/customer-frontend/bonuses`
- history-like link found in DOM summary:
  - `bonuses/changes-history`
- exact interaction path should be revalidated in live UI

### SMK-05 Cart fill and order creation

Priority:
- Critical

Objective:
- verify the user can add goods from supplier catalog to cart and create an order

Preconditions:
- user already in `OnlineDuken`
- at least one supplier and one available product exist

Steps:
1. Open `Каталог`.
2. Select a supplier.
3. Open goods list if required.
4. Add at least one product to cart.
5. Open `Корзина`.
6. Verify selected items.
7. Submit `Создать заказ`.

Expected result:
- item is added to cart
- cart contains expected item
- order creation succeeds
- created order becomes visible in orders flow or success state

Automation notes:
- some deeper supplier interactions still need live validation
- likely requires WebView DOM interaction after context switch

### SMK-06 QR payment using image from gallery

Priority:
- Critical

Objective:
- verify payment can be initiated through QR flow using gallery upload

Preconditions:
- user already in `OnlineDuken`
- valid test QR image exists in emulator gallery/storage

Steps:
1. Open QR payment flow.
2. Select option to upload QR from gallery.
3. Choose QR image.
4. Wait for QR parsing.
5. Verify payment form.
6. Confirm payment.

Expected result:
- QR is successfully recognized
- payment form is populated with valid merchant/payment data
- payment can be completed successfully

Automation notes:
- highest business priority
- requires test QR image from user or prepared artifact
- may involve native gallery picker + WebView flow

### SMK-07 Invoice payment from home

Priority:
- Critical

Objective:
- verify payment by invoice / supplier payment flow from the home page

Preconditions:
- user already in `OnlineDuken`
- valid invoice test data exists

Steps:
1. On home page tap `Оплата`.
2. Open supplier payment page.
3. Choose invoice payment scenario.
4. Enter or select invoice details.
5. Confirm payment.

Expected result:
- payment page opens
- invoice data is accepted
- payment reaches success state or final confirmation stage

Automation notes:
- route observed for supplier payment:
  - `/web/customer-frontend/distributors/qr-distributors`
- tabs found:
  - `Все`
  - `Ручная оплата`
  - `QR оплата`
- exact invoice entry controls still need live validation

## Open Questions For Business / Test Data

Before implementation, it would help to confirm:

1. What exact UI label should be used in smoke for orders:
   - `Заказы`
   - or `Мои заказы`
2. Which supplier should be used as the default supplier for:
   - cart smoke
   - invoice payment smoke
3. Which product should be used as stable smoke data for add-to-cart?
4. Provide one stable QR image for gallery upload tests.
5. Provide stable invoice payment data:
   - supplier
   - invoice number
   - expected amount
   - expected final status

## Recommended Execution Order For Automation

Suggested implementation order:

1. `SMK-01 OnlineDuken entry`
2. `SMK-02 Suppliers are visible in Catalog`
3. `SMK-03 Orders navigation from home`
4. `SMK-04 Bonuses page and bonus history`
5. `SMK-05 Cart fill and order creation`
6. `SMK-07 Invoice payment from home`
7. `SMK-06 QR payment using image from gallery`

Reason:
- start with stable navigation and context switching;
- then move to revenue-critical payment flows once the app shell + WebView automation is stable.
