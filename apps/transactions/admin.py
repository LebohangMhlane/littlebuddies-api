
from apps.transactions.models import Transaction
from django.contrib import admin
import custom_admin_site

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'customer', 'branch', 'status', 'created']
    list_filter = ['status', 'created', 'branch']
    search_fields = ['reference', 'customer__email', 'customer__username']
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.useraccount.is_super_user:
            return [field.name for field in self.model._meta.fields] + ['products_ordered']
        return self.readonly_fields
    
    def has_change_permission(self, request, obj=None):
        if request.user.useraccount.is_super_user:
            return True
        return False
    
    def has_add_permission(self, request):
        return request.user.useraccount.is_super_user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user

custom_admin_site.custom_admin_site.register(Transaction)
