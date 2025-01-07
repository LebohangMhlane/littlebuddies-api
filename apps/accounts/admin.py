from django.contrib import admin
from django.contrib.admin import ModelAdmin

from apps.accounts.models import AccountSetting, UserAccount


class UserAccountAdmin(ModelAdmin):

    def _check_permissions(self, user):
        user_account = user
        if user_account.is_superuser:
            return True
        else:
            return False

    def get_queryset(self, request):
        user = request.user
        user_has_permission = self._check_permissions(user)
        if user_has_permission:
            return super().get_queryset(request)
        else:
            raise PermissionError("You do not have permission to access this page")


admin.site.register(UserAccount, UserAccountAdmin)

admin.site.register(AccountSetting)
