from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    AccountProfile,
    Branch,
    BusinessProfile,
    Category,
    Customer,
    Employee,
    IntegrationConnection,
    Product,
    Role,
    Supplier,
    UserBusinessAccess,
)
from core.views import ensure_default_connections, ensure_default_roles_and_permissions


class Command(BaseCommand):
    help = 'Create safe demo data for testing SMS Suite with a Rwanda-style business.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='owner@example.com')
        parser.add_argument('--password', default='ChangeMe123!')
        parser.add_argument('--business-name', default='Kigali Smart Shop')

    def handle(self, *args, **options):
        ensure_default_roles_and_permissions()
        email = options['email'].strip().lower()
        user, created = User.objects.get_or_create(username=email, defaults={'email': email, 'first_name': 'Demo', 'last_name': 'Owner'})
        if created:
            user.set_password(options['password'])
            user.save(update_fields=['password'])
        AccountProfile.objects.update_or_create(user=user, defaults={'email_verified': True})

        profile, _ = BusinessProfile.objects.get_or_create(
            owner_email=email,
            name=options['business_name'],
            defaults={
                'business_type': 'shop',
                'momo_number': '0780000000',
                'airtel_money_number': '0730000000',
                'whatsapp_number': '0780000000',
                'selected_modules': ['pos', 'inventory', 'customers', 'payments', 'employees', 'expenses', 'suppliers', 'reports', 'integrations'],
                'setup_completed': True,
                'trial_started_at': timezone.now(),
                'trial_ends_at': timezone.now() + timedelta(days=180),
                'subscription_status': 'trial',
            },
        )
        owner_role = Role.objects.get(name='owner')
        UserBusinessAccess.objects.update_or_create(user=user, business=profile, defaults={'email': email, 'role': owner_role, 'is_active': True})
        branch, _ = Branch.objects.get_or_create(profile=profile, name='Main Branch', defaults={'location': 'Kigali', 'phone': '0780000000'})
        categories = {}
        for name in ['General', 'Drinks', 'Food', 'Clothes', 'Pharmacy', 'Services']:
            categories[name], _ = Category.objects.get_or_create(profile=profile, name=name)
        supplier, _ = Supplier.objects.get_or_create(profile=profile, name='Kigali Wholesale Supplier', defaults={'phone': '0781111111', 'location': 'Nyabugogo'})
        Employee.objects.get_or_create(branch=branch, name='Demo Cashier', defaults={'role': 'cashier', 'phone': '0782222222', 'salary': Decimal('120000')})
        Customer.objects.get_or_create(profile=profile, name='Walk-in Customer', defaults={'phone': '', 'email': ''})
        Customer.objects.get_or_create(profile=profile, name='Jean Customer', defaults={'phone': '0783333333', 'email': 'jean@example.com'})
        products = [
            ('MIN-WATER-500', 'Mineral Water 500ml', 'Drinks', 500, 300, 120),
            ('RICE-1KG', 'Rice 1kg', 'Food', 1800, 1400, 60),
            ('TSHIRT-BLK-M', 'Black T-Shirt Medium', 'Clothes', 15000, 9000, 25),
            ('PARA-500', 'Paracetamol 500mg', 'Pharmacy', 1000, 600, 80),
        ]
        for sku, name, category, price, cost, stock in products:
            Product.objects.update_or_create(
                branch=branch,
                sku=sku,
                defaults={
                    'name': name,
                    'category': categories[category],
                    'supplier': supplier,
                    'price': Decimal(str(price)),
                    'cost': Decimal(str(cost)),
                    'stock': stock,
                    'reorder_level': 10,
                    'track_inventory': True,
                    'is_active': True,
                },
            )
        Product.objects.update_or_create(
            branch=branch,
            sku='SERVICE-DELIVERY',
            defaults={
                'name': 'Delivery Service',
                'item_type': 'service',
                'category': categories['Services'],
                'supplier': None,
                'price': Decimal('2000'),
                'cost': Decimal('0'),
                'stock': 0,
                'reorder_level': 0,
                'track_inventory': False,
                'is_active': True,
            },
        )
        ensure_default_connections(profile)
        IntegrationConnection.objects.filter(profile=profile, connection_type__in=['mtn_momo', 'airtel_money']).update(status='needs_setup', notes='Coming soon: keep using manual transaction references until API credentials are approved.')
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write(f'Login email: {email}')
        self.stdout.write(f'Password: {options["password"]}')
