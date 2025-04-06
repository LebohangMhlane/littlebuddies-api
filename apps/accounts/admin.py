from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from apps.accounts.models import AccountSetting, UserAccount
from custom_admin_site import custom_admin_site


class UserAccountAdmin(ModelAdmin):
    list_display = (
        "user",
        "phone_number", 
        "phone_number_verified",
        "email_verified",
        "is_active",
        "is_merchant",
        "is_super_user",
    )
    
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def _check_permissions(self, user):
        user_account = user
        return user_account.is_superuser

    def get_queryset(self, request):
        user = request.user
        user_has_permission = self._check_permissions(user)
        if user_has_permission:
            return super().get_queryset(request)
        else:
            raise PermissionError("You do not have permission to access this page")

custom_admin_site.register(User)
custom_admin_site.register(UserAccount, UserAccountAdmin)
custom_admin_site.register(AccountSetting)
custom_admin_site.register(Token)