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
        token = self.createNormalTestAccountAndLogin()
        self.makeUserAccountSuperAdmin(self.userAccount.pk)
        merchantUserAccount = self.createTestMerchantUserAccount()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 200)
        merchant = Merchant.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEqual(merchant.userAccount.pk, merchantUserAccount.pk)
        self.assertEqual(response.data["merchant"]["name"], createMerchantPayload["name"])
        self.assertTrue(self.userAccount.pk != response.data["merchant"]["userAccount"]["id"])

    def test_unauthorized_create_merchant(self):
        createMerchantPayload = {
            "userAccountPk": 1,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.createNormalTestAccountAndLogin()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 401)
        merchant = Merchant.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEqual(merchant, None)

    def test_deactivate_merchant(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        self.makeUserAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(testMerchantUserAccount)
        self.assertEqual(merchant.isActive, True)
        payload = {
            "merchantId": 1,
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        merchant = Merchant.objects.get(pk=payload["merchantId"])
        self.assertEqual(merchant.isActive, False)

    def test_deactivate_merchant_failure(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        _ = self.makeUserAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(testMerchantUserAccount)
        self.assertEqual(merchant.isActive, True)
        payload = {
            "merchantId": 100, # id doesn't exist
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["message"], "Failed to deactivate merchant")
        self.assertFalse(response.data["success"])
        merchant = Merchant.objects.get(pk=1)
        self.assertEqual(merchant.isActive, True)

    def testUpdateMerchant(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        _ = self.makeUserAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(testMerchantUserAccount)
        self.assertEqual(merchant.name, "Pet Food Shop")
        self.assertEqual(merchant.address, "12 Pet Street Newgermany")
        payload = {
            "merchantPk": 1,
            "name": "World of pets",
            "address": "32 rethman street newgermany",
        }
        updateMerchantUrl = reverse("update_merchant_view")
        response = self.client.post(
            updateMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        updatedMerchant = response.data["updatedMerchant"]
        self.assertEqual(updatedMerchant["name"], "World of pets")
        self.assertEqual(updatedMerchant["address"], "32 rethman street newgermany")