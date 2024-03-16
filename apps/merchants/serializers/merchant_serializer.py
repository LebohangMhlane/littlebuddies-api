
from rest_framework import serializers
from apps.merchants.models import Merchant
from apps.accounts.models import UserAccount


class MerchantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Merchant
        fields = "__all__"
        depth = 2

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        for key, value in initialData.items():
            if value is None or value is "":
                raise Exception("Values must not be empty")
        return True
    
    def create(self, validated_data):
        try:
            merchant = Merchant()
            merchant.user_account = UserAccount.objects.get(pk=validated_data["userAccountPk"])
            merchant.name = validated_data["name"]
            merchant.email = validated_data["email"]
            merchant.address = validated_data["address"]
            merchant.paygateId = validated_data["paygateId"]
            merchant.paygateSecret = validated_data["paygateSecret"]
            merchant.save()
            return merchant
        except Exception as e:
            raise Exception("Failed to create Merchant")