from django.contrib import admin

from apps.orders.models import CancelledOrder, Order, OrderedProduct
import custom_admin_site


custom_admin_site.custom_admin_site.register(Order)
custom_admin_site.custom_admin_site.register(OrderedProduct)
custom_admin_site.custom_admin_site.register(CancelledOrder)
