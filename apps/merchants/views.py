from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.models import UserAccount
from apps.merchants.models import Merchant
from apps.merchants.serializers.merchant_serializer import MerchantSerializer
from apps.products.serializers.serializers import ProductSerializer

class CreateMerchantView(APIView):

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            if not self.checkIfUserHasFullPermissions(request.data):
                return Response({
                    "success": False,
                    "error": "You don't have permission to create Merchants"
                }, status=401)
            self.createMerchant(request.data)
            return Response({
                "success": True,
                "message": "Merchant created successfully"
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    def checkIfUserHasFullPermissions(self, receivedPayload):
        userAccountPk = int(receivedPayload["userAccountPk"])
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        if userAccount.user.is_superuser: 
            if userAccount.can_create_merchants: return True
            else: return False
        else: return False

    def createMerchant(self, receivedPayload):
        merchantSerializer = MerchantSerializer(data=receivedPayload)
        if merchantSerializer.is_valid():
            merchantSerializer.create(validated_data=receivedPayload)


class CreateProductView(APIView):
    
    def get(self, request):
        pass

    def post(self, request):
        try:
            if not self.checkIfUserIsMerchant(request):
                return Response({
                    "success": False,
                    "message": "You are not authorized to create a product"
                }, status=401)
            else:
                product = self.createProduct(request)
            return Response({
                "success": True,
                "message": "Product created successfully",
                "product": product.data
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=500)
    
    def checkIfUserIsMerchant(self, request):
        merchantPk = request.data["merchantPk"]
        merchant = Merchant.objects.get(pk=merchantPk)
        if merchant.user_account == request.user.useraccount:
            return True
        else: return False

    def createProduct(self, request):
        productSerializer = ProductSerializer(data=request.data)
        if productSerializer.is_valid():
            product = productSerializer.create(request.data)
            return ProductSerializer(product, many=False)