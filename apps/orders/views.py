
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.transactions.models import Transaction
from global_view_functions.global_view_functions import GlobalViewFunctions


class GetAllOrdersView(APIView, GlobalViewFunctions):

    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, **kwargs):
        try:
            if self.if_user_is_merchant(request):
                orders = self.get_orders_as_merchant(request)
            else:
                orders = self.get_orders_as_customer(request)
            orders = OrderSerializer(orders, many=True)
            orders = orders.data
            return Response({
                "success": True,
                "message": "Orders retrieved successfully",
                "orders": orders
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get Orders",
                "error": str(e)
            })

    def get_orders_as_merchant(self, request):
        userAccount = request.user.useraccount
        orders = Order.objects.filter(
            transaction__branch__merchant__userAccount__pk=userAccount.pk, 
            transaction__status=Transaction.COMPLETED
        )
        if orders:
            return orders

    def get_orders_as_customer(self, request):
        userAccount = request.user.useraccount
        orders = Order.objects.filter(
            transaction__customer__id=userAccount.pk, 
            transaction__status=Transaction.COMPLETED).order_by("created")
        if orders:
            return orders