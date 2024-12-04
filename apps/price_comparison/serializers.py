from rest_framework import serializers
from apps.products.models import BranchProduct

class BranchProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    branch_name = serializers.CharField(source='branch.merchant.name')
    branch_id = serializers.IntegerField(source='branch.id', read_only=True)  

    class Meta:
        model = BranchProduct
        fields = ['product_name', 'branch_name', 'branch_price', 'storeReference', 'branch_id'] 
