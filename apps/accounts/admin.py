from django.contrib import admin

from apps.accounts.models import AccountSetting, UserAccount

# Register your models here.

admin.site.register(UserAccount)

admin.site.register(AccountSetting)