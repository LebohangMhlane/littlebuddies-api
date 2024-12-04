
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness
from apps.merchants.serializers.merchant_serializer import BranchSerializer
from apps.products.models import BranchProduct, Product

class ProductSerializer(ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        depth = 2

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        initialData = self.cleanFieldsWithNumericalValues(initialData)
        for key, value in initialData.items():
            if value is None or value == "": 
                raise Exception("Fields must not be empty")
        if initialData["originalPrice"] <= 0: 
            raise Exception("Original price cannot be 0 or negative")
        return True            

    def cleanFieldsWithNumericalValues(self, initialData):
        initialData = initialData.copy()
        initialData["merchantPk"] = int(initialData["merchantPk"])
        initialData["originalPrice"] = int(initialData["originalPrice"])
        initialData["discountPercentage"] = int(initialData["discountPercentage"])
        return initialData
    
    def create(self, validated_data, request):
        try:
            merchant = MerchantBusiness.objects.get(pk=validated_data["merchantPk"])
            user_account = request.user.useraccount
            product = Product()
            product.merchant = merchant
            product.name = validated_data["name"]
            product.description = validated_data["description"]
            product.originalPrice = validated_data["originalPrice"]
            product.in_stock = bool(validated_data["in_stock"])
            product.image = validated_data["image"]
            product.store_reference = validated_data["store_reference"]
            product.discountPercentage = validated_data["discountPercentage"]
            product.created_by = user_account
            product.save()
        except Exception as e:
            raise Exception("Failed to create a product")
        return product
    


class BranchProductSerializer(ModelSerializer):

        class Meta:
            model = BranchProduct
            fields = ['id', 'branch_price', 'merchant_name', 'merchant_logo', 'product', 'branch']
            depth = 2

        def is_valid(self, *, raise_exception=False):
            return super().is_valid(raise_exception=raise_exception)
        
        def create(self, validated_data):
            return super().create(validated_data)