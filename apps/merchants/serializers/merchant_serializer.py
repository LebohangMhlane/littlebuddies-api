import traceback
import logging
from django.db import transaction

from rest_framework import serializers
from apps.merchant_wallets.models import MerchantWallet
from apps.merchants.models import Branch, MerchantBusiness, SaleCampaign
from apps.accounts.models import UserAccount

logger = logging.getLogger("littlebuddies")

class MerchantSerializer(serializers.ModelSerializer):

    class Meta:
        model = MerchantBusiness
        fields = ['id', 'name', 'email', 'address', 'logo', 'delivery_fee', 'closing_time']
        depth = 2

    def is_valid(self, *, raise_exception=False):
        initial_data = self.initial_data
        for key, value in initial_data.items():
            if value == None or value == "":
                raise Exception("Values must not be empty")
        return True

    def create_merchant_wallet(self, merchant):
        try:
            merchant_wallet = MerchantWallet()
            merchant_wallet.merchant_business = merchant
            merchant_wallet.save()
            logger.info(f"MerchantWallet created for {merchant.name}")
        except Exception as e:
            logger.exception(f"Failed to create MerchantWallet: {e}")

    def create(self, validated_data):
        try:
            with transaction.atomic():
                merchant = MerchantBusiness()
                merchant.user_account = UserAccount.objects.get(pk=validated_data["user_accountPk"])
                merchant.name = validated_data["name"]
                merchant.email = validated_data["email"]
                merchant.address = validated_data["address"]
                merchant.paygate_id = validated_data["paygateId"]
                merchant.paygate_secret = validated_data["paygateSecret"]
                merchant.delivery_fee = validated_data["deliveryFee"]
                merchant.closing_time = validated_data["closingTime"]
                merchant.save()
                logger.info(f"Merchant created: {merchant.name}")

                if merchant.id:
                    logger.info(f"Creating merchant wallet for: {merchant.name}")
                    self.create_merchant_wallet(merchant)
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


class SaleCampaignSerializer(serializers.ModelSerializer):

    class Meta: 
        model = SaleCampaign
        fields = ['percentage_off', 'branch_product', 'campaign_ends', 'branch']
        depth = 2

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "branch_product" in representation:
            branch_product = representation["branch_product"]
            if branch_product is not None:
                new_discount_price = (float(branch_product["branch_price"]) * (1 - representation["percentage_off"] / 100))
                branch_product["branch_price"] = str(f"{new_discount_price:.2f}")
        return representation

    def is_valid(self, *, raise_exception=False):
        return True

    def create(self, validated_data):
        return super().create(validated_data)
