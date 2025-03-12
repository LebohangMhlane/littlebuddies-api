from django import forms
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

class OrderAdmin(admin.ModelAdmin):

    readonly_fields = (
        "delivery",
        "status",
        "transaction",
        "customer",
        "products_ordered",
    )

    exclude = ["acknowledgement_notification_sent"]

    def get_form(self, request, obj=None, **kwargs):
        """
        Conditionally modify form fields when viewing a single instance.
        """
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.status == "PENDING_PICKUP":
            form.base_fields["delivery_date"].widget = forms.HiddenInput()
            form.base_fields["delivery_address"].widget = forms.HiddenInput()
            form.base_fields["delivery_fee"].widget = forms.HiddenInput()

        return form

    def get_readonly_fields(self, request, obj=None):
        """
        Conditionally make fields read-only based on object state.
        """
        readonly_fields = super().get_readonly_fields(request, obj)

        if obj and obj.status != "PENDING_PICKUP":
            # Add fields to readonly if the status is not PENDING_PICKUP
            readonly_fields += ("delivery_date", "delivery_address", "delivery_fee")

        return readonly_fields

    def change_view(self, request, object_id: str, form_url="", extra_context=None):
        """
        This method is triggered when viewing a single instance in Django Admin.

        :param request: The HTTP request object.
        :param object_id: The ID of the object being viewed.
        :param form_url: The URL for the form (not commonly used).
        :param extra_context: Additional context data for the template.
        """
        instance = self.get_object(request, object_id)
        if instance:
            # do something when viewing one instance:
            if instance.acknowledged and not instance.acknowledgement_notification_sent:
                instance.acknowledgement_notification_sent = True
                instance.save()

        return super().change_view(request, object_id, form_url, extra_context)


custom_admin_site.custom_admin_site.register(Order, OrderAdmin)
custom_admin_site.custom_admin_site.register(OrderedProduct)
custom_admin_site.custom_admin_site.register(CancelledOrder)
