from django.contrib import admin
from apps.orders.models import CancelledOrder, Order, OrderedProduct
from custom_admin_site import custom_admin_site

class OrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'created', 'acknowledged', 'delivery')
    list_filter = ('status', 'acknowledged', 'delivery')
    search_fields = ('transaction__reference', 'transaction__customer__user__first_name', 'transaction__branch__merchant__name')
    readonly_fields = ('created',)
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            readonly_fields.extend([
                'transaction',
                'ordered_products',
                'status',
                'delivery',
                'delivery_fee',
                'deliveryDate',
                'address'
            ])
        return readonly_fields
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(transaction__branch__merchant__user_account=request.user.useraccount)

class OrderedProductAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'branch_product', 'quantity_ordered', 'order_price')
    list_filter = ('branch_product__branch',)
    search_fields = ('branch_product__product__name',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['branch_product', 'sale_campaign', 'quantity_ordered', 'order_price']
        return []
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(branch_product__branch__merchant__user_account=request.user.useraccount)

class CancelledOrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'reason', 'cancelled_at', 'refund_initiated', 'refund_amount')
    list_filter = ('reason', 'refund_initiated')
    search_fields = ('order__transaction__reference', 'cancelled_by__user__first_name')
    readonly_fields = ('cancelled_at',)
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            readonly_fields.extend([
                'order', 
                'cancelled_by',
                'reason',
                'additional_notes',
                'refund_initiated',
                'refund_amount'
            ])
        return readonly_fields
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return qs.filter(order__transaction__branch__merchant__user_account=request.user.useraccount)

custom_admin_site.register(Order, OrderAdmin)
custom_admin_site.register(OrderedProduct, OrderedProductAdmin)
custom_admin_site.register(CancelledOrder, CancelledOrderAdmin)