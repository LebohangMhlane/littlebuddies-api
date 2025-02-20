from custom_admin_site import custom_admin_site
from django.contrib import admin
from django.utils.html import format_html
from apps.products.models import BranchProduct, GlobalProduct
from apps.merchants.models import Branch
from apps.accounts.models import UserAccount

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'recommended_retail_price', 'display_photo')
    search_fields = ('name', 'description')
    
    def display_photo(self, obj):
        if obj.photo:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="object-fit: cover;" /></a>',
                obj.photo.url, 
                obj.photo.url   
            )
        return "No photo"
    display_photo.short_description = 'Photo'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            user_account = request.user.useraccount
            return qs.filter(branchproduct__branch__merchant__user_account=user_account).distinct()
        except UserAccount.DoesNotExist:
            return qs.none()

class BranchProductAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "branch",
        "branch_price",
        "in_stock",
        "is_active",
    )
    list_filter = ("in_stock", "is_active", "branch")
    search_fields = ("product__name", "store_reference")
    readonly_fields = ("created_by",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        try:
            user_account = request.user.useraccount
            return qs.filter(branch__merchant__user_account=user_account)
        except UserAccount.DoesNotExist:
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.useraccount.is_super_user:
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    merchant__user_account=request.user.useraccount
                )
            if db_field.name == "created_by":
                kwargs["queryset"] = UserAccount.objects.filter(user=request.user)
                kwargs["initial"] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # TODO: set read only fields:

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user.useraccount
        super().save_model(request, obj, form, change)

custom_admin_site.register(GlobalProduct, ProductAdmin)
custom_admin_site.register(BranchProduct, BranchProductAdmin)
