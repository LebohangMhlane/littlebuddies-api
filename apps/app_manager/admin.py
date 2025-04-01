from django.contrib import admin

from apps.app_manager.models import AppManager
from custom_admin_site import custom_admin_site


custom_admin_site.register(AppManager)
