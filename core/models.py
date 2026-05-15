from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.urls import reverse


class Branch(models.Model):
    profile = models.ForeignKey('BusinessProfile', on_delete=models.CASCADE, related_name='branches', null=True, blank=True)
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=180)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BusinessProfile(models.Model):
    BUSINESS_CHOICES = [
        ('shop', 'Shop'),
        ('boutique', 'Boutique'),
        ('restaurant', 'Restaurant'),
        ('pharmacy', 'Pharmacy'),
        ('hardware', 'Hardware Store'),
        ('hotel', 'Hotel'),
        ('mini_market', 'Mini Market'),
        ('wholesale', 'Wholesale'),
        ('salon', 'Salon / Barber Shop'),
        ('clinic', 'Clinic / Health Service'),
        ('garage', 'Garage / Auto Repair'),
        ('laundry', 'Laundry / Dry Cleaning'),
        ('construction', 'Construction / Field Service'),
        ('agency', 'Professional Service Agency'),
        ('school', 'School'),
        ('club', 'Club'),
        ('other', 'Other Business'),
    ]

    name = models.CharField(max_length=140, default='Rwanda Business')
    business_type = models.CharField(max_length=40, choices=BUSINESS_CHOICES, default='shop')
    momo_number = models.CharField(max_length=40, blank=True)
    airtel_money_number = models.CharField(max_length=40, blank=True)
    whatsapp_number = models.CharField(max_length=40, blank=True)
    google_sheet_url = models.URLField(blank=True)
    microsoft_excel_url = models.URLField(blank=True)
    offline_mode_enabled = models.BooleanField(default=True)
    selected_modules = models.JSONField(default=list, blank=True)
    owner_email = models.EmailField(blank=True)
    setup_completed = models.BooleanField(default=False)
    plan = models.CharField(max_length=30, default='free_trial')
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_status = models.CharField(max_length=30, default='trial')
    max_branches = models.PositiveIntegerField(default=1)
    max_employees = models.PositiveIntegerField(default=5)
    max_products = models.PositiveIntegerField(default=200)

    @property
    def trial_days_left(self):
        if not self.trial_ends_at:
            return 0
        remaining = self.trial_ends_at.date() - timezone.localdate()
        return max(remaining.days, 0)


    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=60, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.display_name or self.name


class Permission(models.Model):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name or self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')

    class Meta:
        ordering = ['role__name', 'permission__code']
        unique_together = ['role', 'permission']

    def __str__(self):
        return f'{self.role} - {self.permission}'


class UserBusinessAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_accesses', null=True, blank=True)
    email = models.EmailField(blank=True)
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='user_accesses')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='business_accesses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['business__name', 'role__name']
        unique_together = ['user', 'business']

    def __str__(self):
        identity = self.user or self.email or 'Unknown user'
        return f'{identity} - {self.business} ({self.role})'


class AccountProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_profile')
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} profile'


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_verification_codes')
    code_hash = models.CharField(max_length=128)
    email = models.EmailField()
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_active(self):
        return self.used_at is None and timezone.now() <= self.expires_at and self.attempts < 5


class PasswordResetCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_reset_codes')
    code_hash = models.CharField(max_length=128)
    email = models.EmailField()
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_active(self):
        return self.used_at is None and timezone.now() <= self.expires_at and self.attempts < 5


class IntegrationConnection(models.Model):
    TYPE_CHOICES = [
        ('google_sheets', 'Google Sheets'),
        ('excel_online', 'Microsoft Excel Online'),
        ('whatsapp', 'WhatsApp Business'),
        ('offline_excel', 'Offline Excel'),
        ('mtn_momo', 'MTN MoMo'),
        ('airtel_money', 'Airtel Money'),
    ]

    STATUS_CHOICES = [
        ('not_connected', 'Not Connected'),
        ('connected', 'Connected'),
        ('needs_setup', 'Needs Setup'),
    ]

    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='connections')
    connection_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    display_name = models.CharField(max_length=140)
    account_identifier = models.CharField(max_length=220, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='needs_setup')
    sync_direction = models.CharField(max_length=80, default='Import and export')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['connection_type']
        unique_together = ['profile', 'connection_type']

    def __str__(self):
        return self.display_name


class Supplier(models.Model):
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='suppliers', null=True, blank=True)
    name = models.CharField(max_length=140)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
        unique_together = ['profile', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    ITEM_CHOICES = [
        ('product', 'Product'),
        ('service', 'Service'),
    ]

    name = models.CharField(max_length=140)
    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES, default='product')
    sku = models.CharField(max_length=40)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    barcode = models.CharField(max_length=80, blank=True)
    image_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    track_inventory = models.BooleanField(default=True)
    batch_number = models.CharField(max_length=80, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = ['branch', 'sku']

    def __str__(self):
        return f'{self.name} ({self.sku})'

    @property
    def is_low_stock(self):
        return self.track_inventory and self.stock <= self.reorder_level

    @property
    def margin(self):
        return self.price - self.cost


class Customer(models.Model):
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    debt_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loyalty_points = models.PositiveIntegerField(default=0)
    joined_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    ROLE_CHOICES = [
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('stock', 'Stock Controller'),
        ('waiter', 'Waiter'),
        ('housekeeping', 'Housekeeping'),
        ('accountant', 'Accountant'),
        ('staff', 'Staff'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=40, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=40, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.get_role_display()}'


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('mtn_momo', 'MTN MoMo'),
        ('airtel_money', 'Airtel Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('room', 'Room Charge'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    cashier = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='paid')
    reference = models.CharField(max_length=80, blank=True)
    offline_reference = models.CharField(max_length=80, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Sale #{self.pk}'

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal('0.00'))

    @property
    def profit(self):
        return sum((item.profit for item in self.items.all()), Decimal('0.00'))

    @property
    def subtotal(self):
        return self.total

    @property
    def grand_total(self):
        return max(self.subtotal - (self.discount_amount or Decimal('0.00')), Decimal('0.00'))

    def get_absolute_url(self):
        return reverse('sale_detail', args=[self.pk])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['product__name']

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def profit(self):
        return (self.unit_price - self.unit_cost) * self.quantity


class Payment(models.Model):
    METHOD_CHOICES = Sale.PAYMENT_CHOICES
    STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='payments')
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_reference = models.CharField(max_length=100, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.get_method_display()} - {self.amount}'


class Expense(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=140)
    category = models.CharField(max_length=80, default='General')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    spent_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-spent_at']

    def __str__(self):
        return self.title


class StockTransfer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_transfers', null=True, blank=True)
    product_name = models.CharField(max_length=140)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stock_transfers_out')
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stock_transfers_in')
    quantity = models.PositiveIntegerField()
    notes = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product_name}: {self.from_branch} to {self.to_branch}'


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('transfer_out', 'Transfer Out'),
        ('transfer_in', 'Transfer In'),
        ('sale', 'Sale'),
        ('damaged', 'Damaged Stock'),
        ('expired', 'Expired Stock'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product} {self.get_movement_type_display()} {self.quantity}'


class ActivityLog(models.Model):
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    actor = models.CharField(max_length=120, default='System')
    action = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.action


class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='notifications')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_read', '-created_at']

    def __str__(self):
        return self.title


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='purchases')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='purchases')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    invoice_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Purchase #{self.pk or "new"}'


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['product__name']

    @property
    def line_total(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f'{self.product} x {self.quantity}'


class BusinessSubscription(models.Model):
    PLAN_CHOICES = [
        ('free_trial', '6 Month Free Trial'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('business', 'Business'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('expired', 'Expired'),
    ]
    profile = models.OneToOneField(BusinessProfile, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=30, choices=PLAN_CHOICES, default='free_trial')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='trial')
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    max_branches = models.PositiveIntegerField(default=1)
    max_employees = models.PositiveIntegerField(default=5)
    max_products = models.PositiveIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['profile__name']

    def __str__(self):
        return f'{self.profile} - {self.get_plan_display()}'


class CashRegisterSession(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('closed', 'Closed')]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='cash_sessions')
    cashier = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='cash_sessions')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='opened_cash_sessions')
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f'{self.branch} cash session {self.status}'


class BackupLog(models.Model):
    profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='backup_logs', null=True, blank=True)
    filename = models.CharField(max_length=240)
    status = models.CharField(max_length=30, default='created')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.filename


class HospitalityUnit(models.Model):
    UNIT_CHOICES = [
        ('room', 'Hotel Room'),
        ('table', 'Restaurant Table'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('cleaning', 'Cleaning'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='hospitality_units')
    name = models.CharField(max_length=80)
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    current_guest = models.CharField(max_length=120, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['unit_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_unit_type_display()})'

# Create your models here.
