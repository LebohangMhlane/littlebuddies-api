from django.contrib import admin

from apps.orders.models import Order, OrderedProduct
import custom_admin_site


custom_admin_site.custom_admin_site.register(Order)
custom_admin_site.custom_admin_site.register(OrderedProduct)
