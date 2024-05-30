
import traceback

from rest_framework import serializers
from apps.merchants.models import Branch, MerchantBusiness
from apps.accounts.models import UserAccount


class MerchantSerializer(serializers.ModelSerializer):

    class Meta:
        model = MerchantBusiness
        fields = "__all__"
        depth = 2

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        for key, value in initialData.items():
            if value == None or value == "":
                raise Exception("Values must not be empty")
        return True
    
    def create(self, validated_data):
        try:
            merchant = MerchantBusiness()
            merchant.userAccount = UserAccount.objects.get(pk=validated_data["userAccountPk"])
            merchant.name = validated_data["name"]
            merchant.email = validated_data["email"]
            merchant.address = validated_data["address"]
            merchant.paygateId = validated_data["paygateId"]
            merchant.paygateSecret = validated_data["paygateSecret"]
            merchant.save()
            return merchant
        except Exception as e:
            tb = traceback.format_exc()
            raise Exception(f"Failed to create Merchant: {tb}")
        


class BranchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = "__all__"
        depth = 2

    def is_valid(self, *, raise_exception=False):
        return True
    
    def create(self, branchData):
        merchant = MerchantBusiness.objects.get(id=branchData["merchantId"])
        try:
            branch = Branch()
            branch.address = branchData["branchAddress"]
            branch.merchant = merchant
            branch.area = branchData["branchArea"]
            branch.save()
        except Exception as e:
            tb = traceback.format_exc()
            raise Exception(f"Failed to create Branch: {tb}")