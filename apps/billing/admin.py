from django.contrib import admin
from .models import PaymentCategory, Transaction

@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('concept', 'transaction_type', 'amount', 'status', 'issue_date', 'property')
    list_filter = ('transaction_type', 'status', 'category')
    search_fields = ('concept', 'description', 'property__house_number')
    date_hierarchy = 'issue_date'
