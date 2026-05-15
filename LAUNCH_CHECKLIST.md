# SMS Suite Launch Checklist

## Technical
- [ ] PostgreSQL connected through DATABASE_URL
- [ ] DEBUG=0
- [ ] SECRET_KEY is long and private
- [ ] ALLOWED_HOSTS has your domain
- [ ] CSRF_TRUSTED_ORIGINS has your HTTPS domain
- [ ] HTTPS enabled
- [ ] SMTP email tested
- [ ] `python manage.py migrate` completed
- [ ] `python manage.py collectstatic --noinput` completed
- [ ] Daily database backup enabled on host
- [ ] `python manage.py backup_business_data` tested

## Business workflow
- [ ] Owner can register and verify email
- [ ] Owner can complete setup wizard
- [ ] Owner can add branch/team/products/customers/suppliers
- [ ] Stock receiving works
- [ ] POS cart works
- [ ] Receipt printing works
- [ ] WhatsApp receipt link works
- [ ] Debt/partial payment works
- [ ] Daily close works
- [ ] Reports show correct totals
- [ ] Alerts show low stock/expiry/debt

## First customer setup
- [ ] Create owner account
- [ ] Add business details
- [ ] Add 20 real products
- [ ] Add 3 employees with roles
- [ ] Train cashier on POS
- [ ] Print 5 test receipts
- [ ] Close day and compare money
