from django.contrib import admin

from .models import (
    AccountProfile,
    ActivityLog,
    BackupLog,
    Branch,
    BusinessProfile,
    Category,
    Customer,
    EmailVerificationCode,
    Employee,
    Expense,
    HospitalityUnit,
    IntegrationConnection,
    Payment,
    PasswordResetCode,
    Permission,
    Product,
    Purchase,
    PurchaseItem,
    Notification,
    CashRegisterSession,
    BusinessSubscription,
    Role,
    RolePermission,
    Sale,
    SaleItem,
    StockMovement,
    StockTransfer,
    Supplier,
    UserBusinessAccess,
)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'branch', 'customer', 'cashier', 'payment_method', 'created_at', 'total')
    list_filter = ('branch', 'payment_method', 'created_at')
    inlines = [SaleItemInline]


admin.site.register(AccountProfile)
admin.site.register(Branch)
admin.site.register(BusinessProfile)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(EmailVerificationCode)
admin.site.register(Employee)
admin.site.register(Expense)
admin.site.register(Product)
admin.site.register(HospitalityUnit)
admin.site.register(IntegrationConnection)
admin.site.register(Payment)
admin.site.register(PasswordResetCode)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(RolePermission)
admin.site.register(StockMovement)
admin.site.register(StockTransfer)
admin.site.register(Supplier)
admin.site.register(UserBusinessAccess)
admin.site.register(ActivityLog)
admin.site.register(Notification)
admin.site.register(Purchase)
admin.site.register(PurchaseItem)
admin.site.register(BusinessSubscription)
admin.site.register(CashRegisterSession)
admin.site.register(BackupLog)

# Register your models here.
