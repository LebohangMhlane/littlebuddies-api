from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.merchants.models import Merchant
from apps.products.serializers.serializers import ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions



class CreateProductView(APIView, GlobalViewFunctions):
    
    def get(self, request):
        pass

    def post(self, request):
        try:
            exceptionString = "You don't have permission to create a product"
            if not self.checkIfUserBelongsToMerchant(request, exceptionString) and not (
                self.checkIfUserHasFullPermissions(
                    request, exceptionString
                )
            ):
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
                "message": "Failed to create product",
                "exception": str(e)
            }, status=500)

    def createProduct(self, request):
        productSerializer = ProductSerializer(data=request.data)
        if productSerializer.is_valid():
            product = productSerializer.create(request.data)
            return ProductSerializer(product, many=False)
