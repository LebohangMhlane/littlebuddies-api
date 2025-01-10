from django.urls import path

from apps.orders.views import GetAllOrdersView, CancelOrder, RepeatOrder, checkForOrderChangesView

urlpatterns = [
    path("get-all-orders/", GetAllOrdersView.as_view(), name="get_all_orders_view"),
    path("cancel-order/<int:order_id>/", CancelOrder.as_view(), name="cancel_order"),
    path("repeat-order/<int:order_id>/", RepeatOrder.as_view(), name="repeat_order"),
    path(
        "check-for-order-changes/<int:order_id>/",
        checkForOrderChangesView.as_view(),
        name="check_for_order_changes",
    ),
]
