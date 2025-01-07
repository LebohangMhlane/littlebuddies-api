from django.contrib import admin

from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
from apps.products.models import BranchProduct
import custom_admin_site


from django.contrib import admin
from django.db.models import Q

class MerchantBusinessAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user_account__user=request.user)

class BranchAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(merchant__user_account__user=request.user)

class SaleCampaignAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch__merchant__user_account__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    merchant__user_account__user=request.user
                )
            elif db_field.name == "branch_product":
                kwargs["queryset"] = BranchProduct.objects.filter(
                    branch__merchant__user_account__user=request.user
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(MerchantBusiness, MerchantBusinessAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(SaleCampaign, SaleCampaignAdmin)
