from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.products.models import Product
from apps.products.serializers.serializers import ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions



class CreateProductView(APIView, GlobalViewFunctions):

    exceptionString1 = "You don't have permission to create a product"
    
    def get(self, request):
        pass

    def post(self, request):
        try:
            if self.checkIfUserIsMerchant(request):
                if self.checkIfUserMatchesMerchant(request):
                    product = self.createProduct(request)
            elif self.checkIfUserIsSuperAdmin(request):
                product = self.createProduct(request)
            else: raise Exception(self.exceptionString1)
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
            product = productSerializer.create(request.data, request)
            return ProductSerializer(product, many=False)
        

class DeleteProductView(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            if self.checkIfUserIsSuperAdmin(request) or self.checkIfUserIsMerchant(request):
                self.deleteProduct(request, kwargs)
                self.notifyAllOfItemCreation(None)
                return Response({
                    "success": True,
                    "message": "Product deleted successfully",
                })
            else: raise Exception(self.exceptionString1)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to delete Product",
                "exception": str(e)
            })

    def deleteProduct(self, request, kwargs):
        productPk = kwargs["productPk"]
        product = Product.objects.get(pk=productPk)
        if self.checkIfUserIsMerchant(request):
            if self.checkIfUserMatchesProductMerchant(request, product.merchant):
                product.delete()
            else: raise Exception("Merchant account does not match product merchant account")
        else: product.delete()
