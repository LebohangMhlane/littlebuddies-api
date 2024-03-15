

from rest_framework.serializers import ModelSerializer

from merchants.models import Merchant, Product

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
    
    def create(self, validated_data):
        try:
            merchant = Merchant.objects.get(pk=validated_data["merchantPk"])
            product = Product()
            product.merchant = merchant
            product.name = validated_data["name"]
            product.description = validated_data["description"]
            product.original_price = validated_data["originalPrice"]
            product.in_stock = bool(validated_data["inStock"])
            product.image = validated_data["image"]
            product.store_reference = validated_data["storeReference"]
            product.discount_percentage = validated_data["discountPercentage"]
            product.save()
        except Exception as e:
            raise ("Failed to create a product")
        return product