
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions


class GetAllOrdersView(APIView, GlobalViewFunctions):

    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, **kwargs):
        try:
            if self.checkIfUserIsMerchant(request):
                orders = self.getOrdersAsMerchant(request)
            else:
                orders = self.getOrdersAsCustomer(request)
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

    def getOrdersAsMerchant(self, request):
        userAccount = request.user.useraccount
        orders = Order.objects.filter(transaction__merchant__userAccount__pk=userAccount.pk)
        if orders:
            return orders

    def getOrdersAsCustomer(self, request):
        userAccount = request.user.useraccount
        orders = Order.objects.filter(transaction__customer__id=userAccount.pk, status="PENDING")
        if orders:
            return orders