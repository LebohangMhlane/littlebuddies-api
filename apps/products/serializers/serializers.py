

from rest_framework.serializers import ModelSerializer

from apps.accounts.models import UserAccount
from apps.merchants.models import Merchant
from apps.products.models import Product

class ProductSerializer(ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        depth = 2

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        initialData = self.cleanFieldsWithNumericalValues(initialData)
        for key, value in initialData.items():
            if value is None or value is "": 
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
            merchant = Merchant.objects.get(pk=validated_data["merchantPk"])
            userAccount = request.user.useraccount
            product = Product()
            product.merchant = merchant
            product.name = validated_data["name"]
            product.description = validated_data["description"]
            product.originalPrice = validated_data["originalPrice"]
            product.inStock = bool(validated_data["inStock"])
            product.image = validated_data["image"]
            product.storeReference = validated_data["storeReference"]
            product.discountPercentage = validated_data["discountPercentage"]
            product.createdBy = userAccount
            product.save()
        except Exception as e:
            raise Exception("Failed to create a product")
        return product