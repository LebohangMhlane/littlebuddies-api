from django.contrib.admin import ModelAdmin

from apps.accounts.models import AccountSetting, UserAccount
import custom_admin_site


class UserAccountAdmin(ModelAdmin):

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


custom_admin_site.custom_admin_site.register(UserAccount, UserAccountAdmin)

custom_admin_site.custom_admin_site.register(AccountSetting)
