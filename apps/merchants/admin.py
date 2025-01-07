from django.contrib import admin

from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
import custom_admin_site


custom_admin_site.custom_admin_site.register(MerchantBusiness)
custom_admin_site.custom_admin_site.register(Branch)
custom_admin_site.custom_admin_site.register(SaleCampaign)
