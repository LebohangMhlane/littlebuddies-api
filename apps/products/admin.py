from custom_admin_site import custom_admin_site
from django.contrib import admin
from django.utils.html import format_html
from apps.products.models import BranchProduct, GlobalProduct
from apps.merchants.models import Branch
from apps.accounts.models import UserAccount

class GlobalProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'recommended_retail_price']
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.useraccount.is_super_user:
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields
    
    def has_change_permission(self, request, obj=None):
        if request.user.useraccount.is_super_user:
            return True
        return True
    
    def has_add_permission(self, request):
        return request.user.useraccount.is_super_user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user

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
        if request.user.useraccount.is_super_user:
            return qs
        try:
            user_account = request.user.useraccount
            return qs.filter(branchproduct__branch__merchant__user_account=user_account).distinct()
        except UserAccount.DoesNotExist:
            return qs.none()

class BranchProductAdmin(admin.ModelAdmin):
    list_display = (
        "global_product",
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

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)

        if obj and not request.user.useraccount.is_super_user:
            pass # doing nothing here for now:

        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user.useraccount
        super().save_model(request, obj, form, change)

custom_admin_site.register(GlobalProduct, ProductAdmin)
custom_admin_site.register(BranchProduct, BranchProductAdmin)
