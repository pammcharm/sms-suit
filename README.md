# SMS Software Suite

Django business management app for Rwanda SMEs: secure Django login/register, business setup, role-based staff access, POS for products and services, inventory, stock movements, customers, employees, branches, payments, expenses, Excel import/export, WhatsApp/Google Sheets/Excel connector setup, and first-time business onboarding.

## Local Run

```powershell
pip install -r requirements.txt
npm install
npm run css:build
python manage.py migrate
python manage.py runserver
```

Open:

- Tour: `http://127.0.0.1:8000/tour/`
- App: `http://127.0.0.1:8000/auth/`

## Render Deploy

This repo includes:

- `render.yaml`
- `Procfile`
- `build.sh`
- WhiteNoise static setup
- `DATABASE_URL` support for Render PostgreSQL
- compiled Tailwind CSS committed at `static/css/app.css`
- SQLite is local-only fallback; hosted demo data should live in Render PostgreSQL

Steps:

1. Push this project to GitHub.
2. In Render, choose **New +** then **Blueprint**.
3. Connect the GitHub repo.
4. Render reads `render.yaml`, creates the web service and PostgreSQL database.
5. Open `/auth/`, register the owner account, then create the first business workspace.

Do not use SQLite for the Render demo. Render can rebuild app files on deploy, so persistent business data should use the PostgreSQL database created from `render.yaml` through `DATABASE_URL`.

## Accounts and Roles

Owners register with Django email/password login, create a business workspace, then invite employees from Team & Roles. Invited users can register with the same email to access the assigned business.

## Clean Data

The SQLite demo database is ignored by Git. Render will use PostgreSQL and run migrations during build.

## 2026 Production Upgrade Added

This version adds email verification, 6-month free trial fields, stronger onboarding, and better POS partial-payment/debt logic.

After pulling this version, run:

```bash
python manage.py migrate
```

For real email verification in production, configure SMTP environment variables. In development, codes are shown in the console and also on the verification page when `DEBUG=1`.

## Production upgrade notes

See `PRODUCTION_READY_GUIDE.md` and `.env.production.example` before hosting. For Rwanda demo data run:

```bash
python manage.py seed_rwanda_demo --email demo@example.com --password DemoPass123!
```
