from rest_framework.views import APIView
from rest_framework.response import Response

from apps.merchants.models import Merchant
from apps.merchants.serializers.merchant_serializer import MerchantSerializer
from apps.products.serializers.serializers import ProductSerializer

from global_view_functions.global_view_functions import GlobalViewFunctions


class CreateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            exceptionString = "You don't have permission to create merchants"
            if self.checkIfUserHasFullPermissions(request.user.useraccount, exceptionString):
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
        # notify all relevant parties of the creation of a new merchant:
        pass


class DeactivateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            exceptionString = "You don't have permission to deactivate a merchant"
            if self.checkIfUserHasFullPermissions(request.user.useraccount, exceptionString):
                if self.deactivateMerchant(request.data["merchantId"]):
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
        merchant = Merchant.objects.get(pk=int(merchantId))
        merchant.is_active = False
        merchant.save()
        return True
        
    def notifyAllOfDeactivation(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass


class UpdateMerchant(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            exceptionString = "You don't have permission to update a merchant"
            if self.checkIfUserHasFullPermissions(request.user.useraccount, exceptionString):
                if self.updateMerchant(valuesToUpdate=request.data):
                    self.notifyAllOfUpdate()
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
    
    def updateMerchant(self, merchantId, valuesToUpdate):
        merchant = Merchant.objects.get(pk=int(merchantId))
        merchant.is_active = False
        merchant.save()
        return True
        
    def notifyAllOfUpdate(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass





