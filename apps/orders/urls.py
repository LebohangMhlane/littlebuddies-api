from django.urls import path

from apps.orders.views import GetAllOrdersView

urlpatterns = [
    path('get-all-orders/', GetAllOrdersView.as_view(), name="get_all_orders_view"),
]

