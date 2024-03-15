from django.test import TestCase
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig
from merchants.models import Merchant, Product

class MerchantTests(GlobalTestCaseConfig, TestCase):

    def test_create_merchant(self):
        createMerchantPayload = {
            "userAccountPk": 1,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.createTestAccountAndLogin()
        self.makeUserAccountFullAdmin(createMerchantPayload["userAccountPk"])
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEquals(response.status_code, 200)
        merchant = Merchant.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEquals(merchant.name, createMerchantPayload["name"])

    def test_unauthorized_create_merchant(self):
        createMerchantPayload = {
            "userAccountPk": 1,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.createTestAccountAndLogin()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEquals(response.status_code, 401)
        merchant = Merchant.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEquals(merchant, None)
