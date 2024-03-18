from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.merchants.models import Product
from apps.products.serializers.serializers import ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions



class CreateProductView(APIView, GlobalViewFunctions):
    
    def get(self, request):
        pass

    def post(self, request):
        try:
            exceptionString = "You don't have permission to create a product"
            self.checkIfMerchantsMatch(request, exceptionString)
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
        

class DeleteProductView(APIView, GlobalViewFunctions):
    
    def get(self, request, **kwargs):
        try:
            exceptionString = "You do not have permission to delete a product"
            if (self.checkIfUserIsSuperAdmin(request, exceptionString) 
                or self.checkIfMerchantsMatch(request)):
                self.deleteProduct(request, kwargs)
            return Response({
                "success": True,
                "message": "Product deleted successfully",
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to delete Product",
                "exception": str(e)
            })

    def deleteProduct(self, request, kwargs):
        productPk = kwargs["productPk"]
        product = Product.objects.get(pk=productPk)
        self.checkIfMerchantsMatch(request, product.merchant)
        product.delete()
