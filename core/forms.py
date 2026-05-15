from django import forms
import json
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import (
    Branch,
    AccountProfile,
    BusinessProfile,
    EmailVerificationCode,
    Category,
    Customer,
    Employee,
    Expense,
    HospitalityUnit,
    IntegrationConnection,
    Payment,
    Purchase,
    PurchaseItem,
    Product,
    Role,
    Sale,
    StockMovement,
    StockTransfer,
    Supplier,
    UserBusinessAccess,
)


class SaleForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_active=True), required=False)
    quantity = forms.IntegerField(min_value=1, initial=1, required=False)
    cart_items = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Sale
        fields = ['branch', 'customer', 'cashier', 'payment_method', 'reference', 'discount_amount', 'amount_paid']

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        self.fields['discount_amount'].label = 'Discount (RWF)'
        self.fields['amount_paid'].label = 'Amount paid now (RWF)'
        self.fields['reference'].label = 'Payment reference / transaction ID'
        self.fields['amount_paid'].help_text = 'Leave 0 for unpaid/customer debt. Use exact paid amount for partial payments.'
        if profile:
            self.fields['branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
            self.fields['customer'].queryset = Customer.objects.filter(profile=profile)
            self.fields['cashier'].queryset = Employee.objects.filter(branch__profile=profile, is_active=True)
            self.fields['product'].queryset = Product.objects.filter(branch__profile=profile, is_active=True)
        branch_id = None
        if self.data:
            branch_id = self.data.get('branch')
        elif self.initial:
            branch_id = self.initial.get('branch')
        elif self.fields['branch'].queryset.exists():
            branch_id = self.fields['branch'].queryset.first().id
            self.initial['branch'] = branch_id

        if branch_id:
            product_filter = {
                'is_active': True,
                'branch_id': branch_id,
            }
            cashier_filter = {
                'is_active': True,
                'branch_id': branch_id,
            }
            if profile:
                product_filter['branch__profile'] = profile
                cashier_filter['branch__profile'] = profile
            self.fields['product'].queryset = Product.objects.filter(**product_filter).select_related('category', 'branch')
            self.fields['cashier'].queryset = Employee.objects.filter(**cashier_filter)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity') or 0
        discount = cleaned.get('discount_amount') or 0
        amount_paid = cleaned.get('amount_paid') or 0
        cart_items = cleaned.get('cart_items') or ''
        if discount < 0 or amount_paid < 0:
            raise ValidationError('Discount and amount paid cannot be negative.')

        branch = cleaned.get('branch')
        parsed_items = []
        if cart_items:
            try:
                parsed_items = json.loads(cart_items)
            except json.JSONDecodeError:
                raise ValidationError('Cart data is invalid. Refresh the page and try again.')
            if not isinstance(parsed_items, list):
                raise ValidationError('Cart data is invalid. Refresh the page and try again.')
            for row in parsed_items:
                try:
                    product_id = int(row.get('product_id'))
                    qty = int(row.get('quantity'))
                except Exception:
                    raise ValidationError('Every cart item must have a valid product and quantity.')
                if qty <= 0:
                    raise ValidationError('Cart quantity must be greater than zero.')
                item_product = Product.objects.filter(pk=product_id).first()
                if not item_product:
                    raise ValidationError('One product in the cart no longer exists.')
                if branch and item_product.branch_id != branch.id:
                    raise ValidationError(f'{item_product.name} belongs to another branch.')
                if item_product.track_inventory and qty > item_product.stock:
                    raise ValidationError(f'Only {item_product.stock} units of {item_product.name} are available.')
        elif product:
            if product.track_inventory and quantity > product.stock:
                raise ValidationError(f'Only {product.stock} units of {product.name} are available.')
            if branch and product.branch_id != branch.id:
                raise ValidationError('The selected product belongs to another branch.')
        else:
            raise ValidationError('Add at least one product/service to the cart.')

        cashier = cleaned.get('cashier')
        if cashier and branch and cashier.branch_id != branch.id:
            raise ValidationError('The selected employee belongs to another branch.')
        return cleaned


class BusinessProfileForm(forms.ModelForm):
    selected_modules = forms.MultipleChoiceField(
        choices=[
            ('pos', 'POS'),
            ('inventory', 'Inventory'),
            ('customers', 'Customers'),
            ('payments', 'Payments'),
            ('expenses', 'Expenses'),
            ('employees', 'Employees'),
            ('suppliers', 'Suppliers'),
            ('hospitality', 'Hotel & Restaurant'),
            ('transfers', 'Multi-Branch Transfers'),
            ('reports', 'Reports'),
            ('integrations', 'Integrations'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = BusinessProfile
        fields = [
            'name',
            'business_type',
            'momo_number',
            'airtel_money_number',
            'whatsapp_number',
            'google_sheet_url',
            'microsoft_excel_url',
            'offline_mode_enabled',
            'selected_modules',
            'setup_completed',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})
        self.fields['selected_modules'].widget.attrs.pop('class', None)


class ExcelImportForm(forms.Form):
    branch = forms.ModelChoiceField(queryset=None)
    file = forms.FileField(help_text='Upload .xlsx or .csv')

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True, profile=profile) if profile else Branch.objects.none()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['branch', 'title', 'category', 'amount', 'notes']

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            self.fields['branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class StockTransferForm(forms.ModelForm):
    class Meta:
        model = StockTransfer
        fields = ['product', 'from_branch', 'to_branch', 'quantity', 'notes']

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            branches = Branch.objects.filter(profile=profile, is_active=True)
            self.fields['from_branch'].queryset = branches
            self.fields['to_branch'].queryset = branches
            self.fields['product'].queryset = Product.objects.filter(branch__profile=profile, item_type='product', track_inventory=True, is_active=True)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        from_branch = cleaned.get('from_branch')
        to_branch = cleaned.get('to_branch')
        quantity = cleaned.get('quantity') or 0
        if from_branch and to_branch and from_branch == to_branch:
            raise ValidationError('Choose two different branches for a transfer.')
        if product and from_branch and product.branch_id != from_branch.id:
            raise ValidationError('The product must belong to the source branch.')
        if product and quantity > product.stock:
            raise ValidationError(f'Only {product.stock} units of {product.name} are available.')
        return cleaned


class OnboardingForm(BusinessProfileForm):
    branch_name = forms.CharField(max_length=120, initial='Main Branch')
    branch_location = forms.CharField(max_length=180, initial='Kigali')
    branch_phone = forms.CharField(max_length=40, required=False)

    class Meta(BusinessProfileForm.Meta):
        fields = [
            'name',
            'business_type',
            'momo_number',
            'airtel_money_number',
            'whatsapp_number',
            'offline_mode_enabled',
            'selected_modules',
        ]


class IntegrationConnectionForm(forms.ModelForm):
    class Meta:
        model = IntegrationConnection
        fields = ['display_name', 'account_identifier', 'status', 'sync_direction', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'location', 'phone', 'is_active']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'location']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'item_type', 'sku', 'category', 'branch', 'supplier', 'barcode', 'image_url', 'price', 'cost', 'stock', 'reorder_level', 'track_inventory', 'batch_number', 'expiry_date', 'is_active']
        widgets = {'expiry_date': forms.DateInput(attrs={'type': 'date'})}


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'debt_balance', 'credit_balance', 'loyalty_points']


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['branch', 'name', 'role', 'phone', 'salary', 'is_active']


class HospitalityUnitForm(forms.ModelForm):
    class Meta:
        model = HospitalityUnit
        fields = ['branch', 'name', 'unit_type', 'status', 'current_guest', 'daily_rate']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['branch', 'sale', 'method', 'amount', 'status', 'transaction_reference']


class PurchaseForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    quantity = forms.IntegerField(min_value=1, initial=1)
    unit_cost = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    class Meta:
        model = Purchase
        fields = ['branch', 'supplier', 'invoice_number', 'product', 'quantity', 'unit_cost', 'notes']

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            self.fields['branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
            self.fields['supplier'].queryset = Supplier.objects.filter(profile=profile)
            self.fields['product'].queryset = Product.objects.filter(branch__profile=profile, item_type='product', is_active=True)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        branch = cleaned.get('branch')
        if product and branch and product.branch_id != branch.id:
            raise ValidationError('The selected product must belong to the selected branch.')
        return cleaned


class CashCloseForm(forms.Form):
    branch = forms.ModelChoiceField(queryset=Branch.objects.none())
    cashier = forms.ModelChoiceField(queryset=Employee.objects.none(), required=False)
    opening_cash = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, initial=0)
    closing_cash = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            self.fields['branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
            self.fields['cashier'].queryset = Employee.objects.filter(branch__profile=profile, is_active=True)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False, max_length=150)
    last_name = forms.CharField(required=False, max_length=150)

    class Meta:
        model = get_user_model()
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].strip().lower()
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': 'Enter a correct email and password.',
        'inactive': 'This account is inactive.',
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        password = cleaned.get('password')
        if email and password:
            user_model = get_user_model()
            user = user_model.objects.filter(email__iexact=email).first()
            username = user.get_username() if user else email
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise ValidationError(self.error_messages['invalid_login'])
            if not self.user_cache.is_active:
                raise ValidationError(self.error_messages['inactive'])
        return cleaned

    def get_user(self):
        return self.user_cache


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class PasswordResetVerifyForm(forms.Form):
    email = forms.EmailField()
    code = forms.CharField(max_length=6, min_length=6)
    new_password1 = forms.CharField(label='New password', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm new password', widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('new_password1')
        password2 = cleaned.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('The two password fields did not match.')
        if password1:
            validate_password(password1, self.user)
        return cleaned


class EmailVerificationForm(forms.Form):
    code = forms.CharField(label='Verification code', max_length=6, min_length=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = UserBusinessAccess
        fields = ['email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.all()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


class StockMovementForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    movement_type = forms.ChoiceField(choices=[
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('damaged', 'Damaged Stock'),
        ('expired', 'Expired Stock'),
        ('adjustment', 'Stock Adjustment'),
    ])
    quantity = forms.IntegerField(min_value=1)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            self.fields['product'].queryset = Product.objects.filter(branch__profile=profile, item_type='product', track_inventory=True, is_active=True)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})


CRUD_FORMS = {
    'branches': BranchForm,
    'categories': CategoryForm,
    'suppliers': SupplierForm,
    'products': ProductForm,
    'customers': CustomerForm,
    'employees': EmployeeForm,
    'hospitality': HospitalityUnitForm,
    'payments': PaymentForm,
    'expenses': ExpenseForm,
    'transfers': StockTransferForm,
}


for form_class in CRUD_FORMS.values():
    original_init = form_class.__init__

    def styled_init(self, *args, _original_init=original_init, **kwargs):
        profile = kwargs.pop('profile', None)
        _original_init(self, *args, **kwargs)
        if profile:
            scope_form_to_profile(self, profile)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'field'})

    form_class.__init__ = styled_init


def scope_form_to_profile(form, profile):
    if 'branch' in form.fields:
        form.fields['branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
    if 'from_branch' in form.fields:
        form.fields['from_branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
    if 'to_branch' in form.fields:
        form.fields['to_branch'].queryset = Branch.objects.filter(profile=profile, is_active=True)
    if 'category' in form.fields:
        form.fields['category'].queryset = Category.objects.filter(profile=profile)
    if 'supplier' in form.fields:
        form.fields['supplier'].queryset = Supplier.objects.filter(profile=profile)
    if 'sale' in form.fields:
        form.fields['sale'].queryset = Sale.objects.filter(branch__profile=profile)
