from rest_framework import serializers
from apps.products.models import BranchProduct

class BranchProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    branch_name = serializers.CharField(source='branch.merchant.name')

    class Meta:
        model = BranchProduct
        fields = ['product_name', 'branch_name', 'branchPrice', 'storeReference']
