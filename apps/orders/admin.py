from django.contrib import admin

from apps.orders.models import Order, OrderedProduct


admin.site.register(Order)
admin.site.register(OrderedProduct)
