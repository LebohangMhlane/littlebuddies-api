from django.contrib import admin

from apps.orders.models import CancelledOrder, Order, OrderedProduct
import custom_admin_site


class OrderAdmin(admin.ModelAdmin):

    readonly_fields = (
        "acknowledgement_notification_sent",
        "delivery",
        "delivery_date",
        "delivery_address",
        "status",
        "transaction",
        "customer",
        "products_ordered",
        "delivery_fee"
    )

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
