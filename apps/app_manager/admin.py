from django.contrib.admin import ModelAdmin

from apps.app_manager.models import AppManager
from custom_admin_site import custom_admin_site


class AppManagerAdmin(ModelAdmin):

    list_display = ["maintenance_mode_on",]

    def get_queryset(self, request):
        user_account = request.user.useraccount
        user_has_permission = user_account.is_super_user
        if user_has_permission:
            return super().get_queryset(request)
        else:
            raise PermissionError("You do not have permission to access this page")

custom_admin_site.register(AppManager, AppManagerAdmin)
