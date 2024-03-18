from django.test import TestCase
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig
from apps.merchants.models import Merchant

class MerchantTests(GlobalTestCaseConfig, TestCase):

    def test_create_merchant(self):
        createMerchantPayload = {
            "userAccountPk": 2,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.createTestAccountAndLogin()
        self.makeUserAccountFullAdmin(self.userAccount.pk)
        merchantUserAccount = self.createTestMerchantUserAccount()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEquals(response.status_code, 200)
        merchant = Merchant.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEquals(merchant.user_account.pk, merchantUserAccount.pk)
        self.assertEquals(response.data["merchant"]["name"], createMerchantPayload["name"])
        self.assertTrue(self.userAccount.pk != response.data["merchant"]["user_account"]["id"])

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

    def test_deactivate_merchant(self):
        testAccountToken = self.createTestAccountAndLogin()
        self.makeUserAccountFullAdmin(self.userAccount.pk)
        self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant()
        self.assertEquals(merchant.is_active, True)

        payload = {
            "merchantId": 1,
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.data["success"])
        merchant = Merchant.objects.get(pk=payload["merchantId"])
        self.assertEquals(merchant.is_active, False)

    def test_deactivate_merchant_failure(self):
        testAccountToken = self.createTestAccountAndLogin()
        _ = self.makeUserAccountFullAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(testMerchantUserAccount)
        self.assertEquals(merchant.is_active, True)
        payload = {
            "merchantId": 100, # id doesn't exist
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEquals(response.status_code, 500)
        self.assertEqual(response.data["message"], "Failed to deactivate merchant")
        self.assertFalse(response.data["success"])
        merchant = Merchant.objects.get(pk=1)
        self.assertEquals(merchant.is_active, True)

    def testUpdateMerchant(self):
        testAccountToken = self.createTestAccountAndLogin()
        _ = self.makeUserAccountFullAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(testMerchantUserAccount)
        payload = {
            "merchantId": 1,
            "name": "World of pets",
            "address": "32 rethman street newgermany",
        }
        updateMerchantUrl = reverse("update_merchant_view")
        response = self.client.post(
            updateMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )