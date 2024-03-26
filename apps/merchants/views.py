from rest_framework.views import APIView
from rest_framework.response import Response

from apps.integrations.firebase_instance.firebase_instance_module import FirebaseInstance
from apps.merchants.models import MerchantBusiness
from apps.merchants.serializers.merchant_serializer import MerchantSerializer

from apps.orders.models import Order
from global_view_functions.global_view_functions import GlobalViewFunctions


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
                "exception": str(e)
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
                "exception": str(e)
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
                "exception": str(e)
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


class AcknowledgedOrderView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        try:
            if self.checkIfUserIsMerchant(request):
                orderPk = kwargs["orderPk"]
                order = Order.objects.filter(pk=orderPk).first()
                notificationSent = self.sendNotificationOfOrderAcknowledgement(order)
                if not notificationSent:
                    self.sendAcknowledgementEmail(order)
            else: raise Exception("You're not permitted to use this feature")
            return Response({
                "success": True,
                "message": "Order acknowledged successfully",
            }, status=200)
        except Exception as e:
            return Response({
                "sucess": False,
                "message": "Failed to acknowledge order",
                "error": str(e)
            }, status=500)
        
    def sendNotificationOfOrderAcknowledgement(self, order):
        notificationSent = FirebaseInstance().sendOrderAcknowledgementNotification(order)
        return notificationSent
    
    def sendAcknowledgementEmail(self):
        pass




