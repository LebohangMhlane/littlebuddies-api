from django import forms
from django.contrib import admin
from apps.orders.models import CancelledOrder, Order, OrderedProduct
from custom_admin_site import custom_admin_site

class OrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'created', 'acknowledged', 'delivery')
    list_filter = ('status', 'acknowledged', 'delivery')
    search_fields = ('transaction__reference', 'transaction__customer__user__first_name', 'transaction__branch__merchant__name')
    readonly_fields = ('created',)
    exclude = ["acknowledgement_notification_sent"]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Hide delivery-related fields for pickup orders
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
        
        if obj:  # editing an existing object
            readonly_fields.extend([
                'transaction',
                'customer',
                'products_ordered',
                'status',
                'delivery',
            ])
            
            # Make delivery-related fields read-only if it's a delivery order
            if obj.delivery:
                readonly_fields.extend([
                    'delivery_fee',
                    'delivery_date',
                    'delivery_address',
                ])
                
        return readonly_fields
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # For pickup orders, create fieldsets that exclude delivery fields
        if obj and not obj.delivery:
            fields = [field for field in self.get_fields(request, obj) 
                     if field not in ['delivery_fee', 'delivery_date', 'delivery_address']]
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


custom_admin_site.register(Order, OrderAdmin)
custom_admin_site.register(OrderedProduct)
custom_admin_site.register(CancelledOrder)
