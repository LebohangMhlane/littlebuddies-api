from django.urls import path

from apps.orders.views import GetAllOrdersView, CancelOrder, RepeatOrder

urlpatterns = [
    path("get-all-orders/", GetAllOrdersView.as_view(), name="get_all_orders_view"),
    path("cancel-order/<int:order_id>/", CancelOrder.as_view(), name="cancel-order"),
    path("repeat-order/<int:order_id>/", RepeatOrder.as_view(), name="repeat-order"),
]
