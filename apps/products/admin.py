from custom_admin_site import custom_admin_site
from django.contrib import admin
from django.utils.html import format_html
from apps.products.models import BranchProduct, GlobalProduct
from apps.merchants.models import Branch

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'recommended_retail_price', 'display_photo')
    search_fields = ('name', 'description')
    
    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.photo.url)
        return "No photo"
    display_photo.short_description = 'Photo'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branchproduct__branch__merchant__users=request.user).distinct()

class BranchProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'branch', 'merchant_name', 'branch_price', 'in_stock', 'is_active')
    list_filter = ('in_stock', 'is_active', 'branch')
    search_fields = ('product__name', 'merchant_name', 'store_reference')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch__merchant__users=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(merchant__users=request.user)
            elif db_field.name == "product":
                kwargs["queryset"] = GlobalProduct.objects.filter(
                    branchproduct__branch__merchant__users=request.user
                ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user.useraccount
        super().save_model(request, obj, form, change)

custom_admin_site.register(GlobalProduct, ProductAdmin)
custom_admin_site.register(BranchProduct, BranchProductAdmin)