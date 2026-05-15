from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import ActivityLog, Branch, BusinessProfile, Category, Customer, Employee, Expense, HospitalityUnit, IntegrationConnection, Payment, Product, Sale, SaleItem, Supplier


class Command(BaseCommand):
    help = 'Seed the SMS demo with realistic business data.'

    def handle(self, *args, **options):
        profile, _ = BusinessProfile.objects.get_or_create(
            name='Kigali Smart Retail',
            defaults={
                'business_type': 'mini_market',
                'momo_number': '+250 78 000 1000',
                'airtel_money_number': '+250 73 000 2000',
                'whatsapp_number': '+250 78 000 3000',
                'selected_modules': ['pos', 'inventory', 'customers', 'payments', 'employees', 'expenses', 'reports', 'integrations'],
                'setup_completed': True,
            }
        )
        branches = [
            Branch.objects.get_or_create(profile=profile, name='Central City Branch', defaults={'location': 'Kigali Downtown', 'phone': '+250 78 100 2000'})[0],
            Branch.objects.get_or_create(profile=profile, name='Airport Hotel Branch', defaults={'location': 'Kigali Airport Road', 'phone': '+250 78 300 4000'})[0],
        ]
        for key, name in [
            ('google_sheets', 'Google Sheets'),
            ('excel_online', 'Microsoft Excel Online'),
            ('whatsapp', 'WhatsApp Business'),
            ('offline_excel', 'Offline Excel'),
            ('mtn_momo', 'MTN MoMo'),
            ('airtel_money', 'Airtel Money'),
        ]:
            IntegrationConnection.objects.get_or_create(profile=profile, connection_type=key, defaults={'display_name': name, 'status': 'needs_setup'})
        supplier, _ = Supplier.objects.get_or_create(profile=profile, name='Kigali Wholesale Supply', defaults={'phone': '+250 78 700 7000', 'location': 'Nyabugogo'})

        categories = {
            name: Category.objects.get_or_create(profile=profile, name=name)[0]
            for name in ['Groceries', 'Beverages', 'Restaurant', 'Hotel Services', 'Electronics']
        }

        customers = [
            Customer.objects.get_or_create(profile=profile, name='Amina Uwase', defaults={'phone': '+250 78 222 1199', 'email': 'amina@example.com', 'loyalty_points': 430})[0],
            Customer.objects.get_or_create(profile=profile, name='Jean Claude Niyonsenga', defaults={'phone': '+250 78 444 8300', 'email': 'jean@example.com', 'loyalty_points': 180})[0],
            Customer.objects.get_or_create(profile=profile, name='Sarah Mukamana', defaults={'phone': '+250 78 555 1010', 'email': 'sarah@example.com', 'loyalty_points': 760})[0],
        ]

        employees = [
            Employee.objects.get_or_create(name='Thabo Nkosi', branch=branches[0], defaults={'role': 'manager', 'phone': '+27 60 100 1001', 'salary': Decimal('18500')})[0],
            Employee.objects.get_or_create(name='Lerato Khumalo', branch=branches[0], defaults={'role': 'cashier', 'phone': '+27 60 100 1002', 'salary': Decimal('9200')})[0],
            Employee.objects.get_or_create(name='Priya Singh', branch=branches[1], defaults={'role': 'waiter', 'phone': '+27 60 100 1003', 'salary': Decimal('8700')})[0],
            Employee.objects.get_or_create(name='Jonas Mbeki', branch=branches[1], defaults={'role': 'housekeeping', 'phone': '+27 60 100 1004', 'salary': Decimal('8100')})[0],
        ]

        product_rows = [
            ('Premium Rice 10kg', 'GRC-001', 'Groceries', branches[0], '189.99', '132.00', 42, 12),
            ('Sparkling Water 500ml', 'BEV-014', 'Beverages', branches[0], '16.50', '8.20', 120, 30),
            ('Bluetooth Scanner', 'ELC-221', 'Electronics', branches[0], '699.00', '480.00', 6, 8),
            ('Chef Breakfast Plate', 'RST-110', 'Restaurant', branches[1], '95.00', '42.00', 35, 10),
            ('House Red Wine', 'BEV-077', 'Beverages', branches[1], '88.00', '51.00', 22, 8),
            ('Deluxe Room Night', 'HTL-501', 'Hotel Services', branches[1], '1250.00', '620.00', 12, 3),
        ]
        products = []
        for name, sku, category, branch, price, cost, stock, reorder in product_rows:
            product, _ = Product.objects.get_or_create(
                branch=branch,
                sku=sku,
                defaults={
                    'name': name,
                    'category': categories[category],
                    'supplier': supplier,
                    'price': Decimal(price),
                    'cost': Decimal(cost),
                    'stock': stock,
                    'reorder_level': reorder,
                },
            )
            products.append(product)

        unit_rows = [
            ('Room 101', 'room', 'occupied', 'Sarah Mokoena', '980.00', branches[1]),
            ('Room 204', 'room', 'cleaning', '', '1250.00', branches[1]),
            ('Table 4', 'table', 'reserved', 'Naidoo Party', '0.00', branches[1]),
            ('Table 9', 'table', 'available', '', '0.00', branches[1]),
        ]
        for name, unit_type, status, guest, rate, branch in unit_rows:
            HospitalityUnit.objects.get_or_create(
                name=name,
                branch=branch,
                defaults={'unit_type': unit_type, 'status': status, 'current_guest': guest, 'daily_rate': Decimal(rate)},
            )

        if not Sale.objects.exists():
            for index, product in enumerate(products[:4]):
                sale = Sale.objects.create(
                    branch=product.branch,
                    customer=customers[index % len(customers)],
                    cashier=employees[index % len(employees)],
                    payment_method=['mtn_momo', 'cash', 'airtel_money', 'room'][index],
                )
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=index + 1,
                    unit_price=product.price,
                    unit_cost=product.cost,
                )
                Payment.objects.create(branch=sale.branch, sale=sale, method=sale.payment_method, amount=sale.total, status='matched')

        if not Expense.objects.exists():
            Expense.objects.create(branch=branches[0], title='Internet bundle', category='Operations', amount=Decimal('25000'))
            Expense.objects.create(branch=branches[1], title='Kitchen gas refill', category='Restaurant', amount=Decimal('42000'))

        if not ActivityLog.objects.exists():
            ActivityLog.objects.create(profile=profile, branch=branches[0], action='Demo data seeded for Rwanda SMS workflow')

        self.stdout.write(self.style.SUCCESS('SMS demo data is ready.'))
