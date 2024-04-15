import googlemaps.client
import googlemaps.distance_matrix
import googlemaps.geolocation
from rest_framework.views import APIView
from rest_framework.response import Response

import googlemaps

from apps.integrations.firebase_integration.firebase_module import FirebaseInstance
from apps.merchants.models import MerchantBusiness
from apps.merchants.serializers.merchant_serializer import MerchantSerializer

from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions


class getMerchants(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            # TODO: restrict api key access to server ip address:
            gmaps = googlemaps.Client(key="AIzaSyBQgPeIoIWjNxRWzwKoLJhHO5yUyUcTLXo")

            distance = googlemaps.distance_matrix.distance_matrix(
                client=gmaps,
                origins=["71 Rethman Street, New Germany, 3610"],
                destinations=["Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640"]
            )

            deviceLocation = kwargs["coordinates"]

            return Response({
                "success": True,
                "message": "Stores near customer retrieved successfully",
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=401)



class CreateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            if self.checkIfUserIsSuperAdmin(request):
                merchant = self.createMerchant(request.data)
                if merchant:
                    self.notifyAllOfMerchantCreation()
            return Response({
                "success": True,
                "message": "Merchant created successfully",
                "merchant": merchant.data
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to create merchant",
                "error": str(e)
            }, status=401)

    def createMerchant(self, receivedPayload):
        merchantSerializer = MerchantSerializer(data=receivedPayload)
        if merchantSerializer.is_valid():
            merchant = merchantSerializer.create(validated_data=receivedPayload)
            return MerchantSerializer(merchant, many=False)
        
    def notifyAllOfMerchantCreation(self):
        # TODO: notify all relevant parties of the creation of a new merchant:
        pass


class DeactivateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if request.user.useraccount.canCreateMerchants:
                self.deactivateMerchant(request.data["merchantId"])
                self.notifyAllOfDeactivation()
                return Response({
                    "success": True,
                    "message": "merchant deactivated successfully"
                }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to deactivate merchant",
                "error": str(e)
            }, status=500)
    
    def deactivateMerchant(self, merchantId):
        merchant = MerchantBusiness.objects.get(pk=int(merchantId))
        merchant.isActive = False
        merchant.save()
        
    def notifyAllOfDeactivation(self):
        # TODO: send emails to relevant parties notifiying them of the deactivation:
        pass


class UpdateMerchant(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if self.checkIfUserIsSuperAdmin(request):
                updatedMerchant = self.updateMerchant(request)
                merchantSerializer = MerchantSerializer(updatedMerchant, many=False)
                self.notifyAllOfUpdate()
                return Response({
                    "success": True,
                    "message": "Merchant updated successfully",
                    "updatedMerchant": merchantSerializer.data
                }, status=200)
            else: raise Exception(self.exceptionString2)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to deactivate merchant",
                "error": str(e)
            }, status=500)
    
    def updateMerchant(self, request):
        receivedPayload = request.data.copy()
        merchant = MerchantBusiness.objects.get(pk=int(receivedPayload["merchantPk"]))
        del receivedPayload["merchantPk"]
        for key, value in receivedPayload.items():
            self.validateKey(key)
            merchant.__setattr__(key, value)
        merchant.save()
        return merchant
    
    def validateKey(self, key):
        if (key == "fernetToken"):
            raise Exception("FernetToken cannot be modified")
        
    def notifyAllOfUpdate(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass


class AcknowledgeOrderView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        try:
            if self.checkIfUserIsMerchant(request):
                orderPk = kwargs["orderPk"]
                order = Order.objects.filter(pk=orderPk).first()
                notificationSent = self.sendNotificationOfOrderAcknowledgement(order)
                if not notificationSent:
                    self.sendAcknowledgementEmail(order)
                order.acknowledged = True
                order.save()
            else: raise Exception("You're not permitted to use this feature")
            return Response({
                "success": True,
                "message": "Order acknowledged successfully",
            }, status=200)
        except Exception as e:
            self.sendAcknowledgementEmail(order)
            return Response({
                "sucess": False,
                "message": "Failed to acknowledge order",
                "error": str(e)
            }, status=500)
        
    def sendNotificationOfOrderAcknowledgement(self, order):
        notificationSent = FirebaseInstance().sendOrderAcknowledgementNotification(order)
        return notificationSent
    
    def sendAcknowledgementEmail(self, order:Order):
        pass


class FulfillOrderView(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            orderPk = kwargs["orderPk"]
            if self.checkIfUserIsMerchant(request):
                order = self.fulfillOrder(orderPk)
                orderSerializer = OrderSerializer(order, many=False)
            else: raise Exception("You don't have permission to access this feature.")
            return Response({
                "success": True,
                "message": "Order fulfilled successfully",
                "order": orderSerializer.data,
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to fulfill order",
                "error": str(e)
            })
        
    def fulfillOrder(self, orderPk):
        order = Order.objects.filter(pk=orderPk).first()
        if order:
            order.status = Order.DELIVERED
            order.save()
            return order
        else: raise Exception("This order was not found")



