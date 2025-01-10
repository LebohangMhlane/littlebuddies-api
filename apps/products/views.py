from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.products.models import BranchProduct, GlobalProduct
from apps.products.serializers.serializers import ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions



class CreateProductView(APIView, GlobalViewFunctions):

    exceptionString1 = "You don't have permission to create a product"
    
    def get(self, request):
        pass

    def post(self, request):
        try:
            if self.if_user_is_merchant(request):
                if self.if_user_is_owner(request):
                    product = self.create_product(request)
            elif self.if_user_is_super_admin(request):
                product = self.create_product(request)
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
                "error": str(e)
            }, status=500)

    def create_product(self, request):
        productSerializer = ProductSerializer(data=request.data)
        if productSerializer.is_valid():
            product = productSerializer.create(request.data, request)
            return ProductSerializer(product, many=False)
        

class DeleteProductView(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            if self.if_user_is_super_admin(request) or self.if_user_is_merchant(request):
                self.deleteProduct(request, kwargs)
                self.notify_all_of_item_creation(None)
                return Response({
                    "success": True,
                    "message": "Product deleted successfully",
                })
            else: raise Exception(self.exceptionStrings[0])
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to delete Product",
                "error": str(e)
            })

    def deleteProduct(self, request, kwargs):
        productPk = kwargs["productPk"]
        product = BranchProduct.objects.get(pk=productPk)
        if self.if_user_is_merchant(request):
            if self.check_if_user_matches_product_merchant(request, product.merchant):
                product.delete()
            else: raise Exception("Merchant account does not match product merchant account")
        else: product.delete()
