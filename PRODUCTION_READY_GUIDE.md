# SMS Suite Production Guide

SMS Suite is now prepared for a real deployment. Hosting is the only remaining step, but production still requires correct environment variables, PostgreSQL, HTTPS, backups, and real email credentials.

## What was added/fixed

- Fixed form errors in Expenses, Team, Transfers, and Stock Movements.
- Upgraded POS from single-item sale to cart-based sale.
- Added partial payment, unpaid payment, customer debt, and customer credit handling.
- Added WhatsApp receipt link from receipt page.
- Added 6-month free trial fields and setup wizard enforcement.
- Added email verification and password reset code flow.
- Added production environment example file.
- Added health check endpoint: `/health/`.
- Added Rwanda demo seed command.
- Added production logging and safer security settings.
- Added damaged/expired stock movement types.
- Kept MTN MoMo and Airtel Money as coming-soon integrations with manual reference support.

## Production setup steps

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.production.example .env
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver
```

For demo/testing data:

```bash
python manage.py seed_rwanda_demo --email demo@example.com --password DemoPass123!
```

## Required production services

1. PostgreSQL database
2. SMTP email provider
3. Domain name
4. HTTPS certificate
5. Daily database backup
6. Error log monitoring

## Business usage flow

Owner registers -> verifies email -> creates business -> setup wizard creates branch/category/integrations -> owner adds products/services/customers/employees -> cashier sells through POS -> stock reduces -> receipt is generated -> WhatsApp receipt can be sent -> dashboard/report shows sales, profit, debt, and stock.

## Best businesses for Rwanda

- Boutique
- Pharmacy
- Mini market
- Hardware shop
- Salon/barber
- Restaurant
- Electronics shop
- Garage
- Wholesale
- Service company
- School supplier
- Hotel/guest house

## Important before charging real businesses

Test with 2-3 real shops manually before public launch. Watch: POS speed, stock accuracy, debt accuracy, receipt format, employee permissions, and email delivery.

## New fast-ready features added in this version

- Printable receipt page with browser print support for A4 and thermal-style receipts.
- Purchases & Stock Receiving page: receive product stock from supplier and update inventory automatically.
- Daily Cash Closing page: compare expected cash with actual closing cash.
- Alerts center: low stock, expiry warning, customer debt, and trial ending alerts.
- Backup center and `backup_business_data` command for emergency JSON exports.
- Better reports: revenue, gross profit, expenses, net profit, customer debt, purchases, payment mix, and top products.
- More production models: Purchase, PurchaseItem, Notification, CashRegisterSession, BusinessSubscription, BackupLog.

## Before first real shop uses it

Run these commands:

```bash
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py backup_business_data
```

Then test these flows with real sample data:

1. Register owner and verify email.
2. Complete setup wizard.
3. Add branch, supplier, customer, employee, products.
4. Receive stock through Purchases.
5. Sell 3+ products through POS cart.
6. Print receipt.
7. Send WhatsApp receipt.
8. Record expense.
9. Run Daily Close.
10. Check Reports and Alerts.

## Production warning

`python manage.py check --deploy` will warn if your local environment has DEBUG=1 or no real secret/domain. On the host, set the values from `.env.production.example` and the warnings should be resolved.
