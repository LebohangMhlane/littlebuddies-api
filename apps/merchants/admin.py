from django.contrib import admin

from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign

# Register your models here.

admin.site.register(MerchantBusiness)
admin.site.register(Branch)
admin.site.register(SaleCampaign)
