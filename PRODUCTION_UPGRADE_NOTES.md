# SMS Suite Upgrade Notes

This ZIP includes practical production-readiness upgrades added to your existing Django project.

## Added

- Email verification after registration/login.
- Verification code page at `/verify-email/`.
- AccountProfile model to store `email_verified`.
- 6-month trial fields on each business:
  - `plan`
  - `trial_started_at`
  - `trial_ends_at`
  - `subscription_status`
  - `max_branches`
  - `max_employees`
  - `max_products`
- Onboarding wizard improvements:
  - First branch name/location/phone fields.
  - Trial starts when setup is completed.
- POS payment improvements:
  - Discount amount.
  - Amount paid now.
  - Automatic Paid / Partial / Unpaid status.
  - Automatic customer debt balance when not fully paid.
  - Automatic customer credit balance when overpaid.
- WhatsApp receipt flow remains link-based for MVP.
- MTN MoMo and Airtel Money remain manual/coming-soon integrations until API credentials are ready.

## Run after unzipping

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Production email setup

Set these environment variables on Render/Railway/VPS:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_google_app_password
EMAIL_USE_TLS=1
DEFAULT_FROM_EMAIL="SMS Suite <your_email@gmail.com>"
```

Better production providers later:

- Brevo
- Resend
- SendGrid
- Mailgun

## Production security settings

```bash
DEBUG=0
SECURE_SSL_REDIRECT=1
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
SECURE_HSTS_SECONDS=31536000
```

## Next big improvements

1. Real cart POS with multiple products per sale.
2. Subscription billing page.
3. WhatsApp Business Cloud API.
4. MTN MoMo API collection.
5. Airtel Money API collection.
6. Cash register sessions/daily close.
7. Stock purchases and supplier invoices.
8. Refunds and returns.
9. Audit logs for every important action.
