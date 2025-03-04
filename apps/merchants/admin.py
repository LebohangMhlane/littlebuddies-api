from django.contrib import admin

from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
from apps.products.models import BranchProduct
from custom_admin_site import custom_admin_site


from django.contrib import admin

class MerchantBusinessAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "address",
        "is_active",
    )
    
    def get_exclude(self, request, obj=None):
        if request.user.useraccount.is_super_user:
            return []
        return [
            "fernet_token",
            "paygate_secret",
            "logo",
            "paygate_id",
            "user_account",
        ]

    def get_readonly_fields(self, request, obj=None):
        if request.user.useraccount.is_super_user:
            return []
        return [
            "name",
            "email",
            "address",
            "is_active",
            "paygate_reference",
            "delivery_fee",
            "closing_time",
        ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(user_account__user=request.user)

class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "address",
        "is_active",
        "merchant",
    )

    readonly_fields = ("merchant", "address", "area")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            self.readonly_fields = ()
            return qs
        return qs.filter(merchant__user_account__user=request.user)

class SaleCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "branch_product",
        "percentage_off",
        "active",
        "campaign_ends",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(branch__merchant__user_account__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.useraccount.is_super_user:
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    merchant__user_account__user=request.user
                )
            elif db_field.name == "branch_product":
                kwargs["queryset"] = BranchProduct.objects.filter(
                    branch__merchant__user_account__user=request.user
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

custom_admin_site.register(MerchantBusiness, MerchantBusinessAdmin)
custom_admin_site.register(Branch, BranchAdmin)
custom_admin_site.register(SaleCampaign, SaleCampaignAdmin)
