from django import forms
from django.contrib import admin
from apps.orders.models import CancelledOrder, Order, OrderedProduct
from custom_admin_site import custom_admin_site
from django.utils.html import format_html


class OrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'created', 'acknowledged', 'delivery')
    list_filter = ('status', 'acknowledged', 'delivery')
    search_fields = ('transaction__reference', 'transaction__customer__user__first_name', 'transaction__branch__merchant__name')
    readonly_fields = ('created',)
    exclude = ["acknowledgement_notification_sent"]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj and not obj.delivery:  # If it's a pickup order
            if "delivery_fee" in form.base_fields:
                form.base_fields["delivery_fee"].widget = forms.HiddenInput()
            if "delivery_date" in form.base_fields:
                form.base_fields["delivery_date"].widget = forms.HiddenInput()
            if "delivery_address" in form.base_fields:
                form.base_fields["delivery_address"].widget = forms.HiddenInput()

        return form
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        
        if obj:  
            readonly_fields.extend([
                'transaction',
                'customer',
                'products_ordered',
                'status',
                'delivery',
            ])
            
            if obj.delivery:
                readonly_fields.extend([
                    'delivery_fee',
                    'delivery_date',
                    'delivery_address',
                ])
                
        return readonly_fields
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj and not obj.delivery:
            fields = [field for field in self.get_fields(request, obj) if field not in ['delivery_fee', 'delivery_date', 'delivery_address']]
            return [(None, {'fields': fields})]
            
        return fieldsets
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(transaction__branch__merchant__user_account=request.user.useraccount)
        
    def change_view(self, request, object_id, form_url="", extra_context=None):
        instance = self.get_object(request, object_id)
        if instance:
            # Send notification if acknowledged but notification not sent
            if instance.acknowledged and not instance.acknowledgement_notification_sent:
                instance.acknowledgement_notification_sent = True
                instance.save()

        return super().change_view(request, object_id, form_url, extra_context)
    
    def has_add_permission(self, request):
        return request.user.useraccount.is_super_user
    
    def has_change_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user
    
class OrderedProductAdmin(admin.ModelAdmin):

    list_display = (
        "branch_product",
        "sale_campaign",
        "quantity_ordered",
        "order_price",
        "display_photo",
    )
    list_filter = ("quantity_ordered", "order_price",)
    search_fields = (
        "branch_product",
        "quantity_ordered",
        "order_price",
    )
    readonly_fields = ()
    exclude = []

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(branch_product__branch__merchant__user_account=request.user.useraccount)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)

        # no one should be able to edit a ordered product:
        if obj:  
            readonly_fields.extend(
                [
                    "branch_product",
                    "sale_campaign",
                    "quantity_ordered",
                    "order_price",
                ]
            )

        return readonly_fields
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj = ...):
        return False

    def has_delete_permission(self, request, obj = ...):
        return False

    def display_photo(self, obj):
        if obj.branch_product.global_product.photo:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="object-fit: cover;" /></a>',
                obj.branch_product.global_product.photo.url,
                obj.branch_product.global_product.photo.url,
            )
        return format_html("<span>No photo</span>")

    display_photo.short_description = "Photo"

class CancelledOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'cancelled_by', 'cancelled_at', 'reason', 'refund_initiated')
    list_filter = ('reason', 'refund_initiated', 'cancelled_at')
    search_fields = ('order__transaction__reference', 'additional_notes')
    readonly_fields = ('cancelled_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(order__transaction__branch__merchant__user_account=request.user.useraccount)
    
    def has_add_permission(self, request):
        return request.user.useraccount.is_super_user
    
    def has_change_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.useraccount.is_super_user

custom_admin_site.register(CancelledOrder, CancelledOrderAdmin)
custom_admin_site.register(Order, OrderAdmin)
custom_admin_site.register(OrderedProduct, OrderedProductAdmin)
