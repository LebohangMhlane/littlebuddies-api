from unittest.mock import patch
from django.test import TestCase
from rest_framework.reverse import reverse

from apps.orders.models import Order
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse
from apps.merchants.models import MerchantBusiness


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
        self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        merchantUserAccount = self.createTestMerchantUserAccount()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 200)
        merchant = MerchantBusiness.objects.filter(name=createMerchantPayload["name"]).first()
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
        merchant = MerchantBusiness.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEqual(merchant, None)

    def test_deactivate_merchant(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(testMerchantUserAccount)
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
        merchant = MerchantBusiness.objects.get(pk=payload["merchantId"])
        self.assertEqual(merchant.isActive, False)

    def test_deactivate_merchant_failure(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        _ = self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(testMerchantUserAccount)
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
        merchant = MerchantBusiness.objects.get(pk=1)
        self.assertEqual(merchant.isActive, True)

    def test_update_merchant(self):
        testAccountToken = self.createNormalTestAccountAndLogin()
        _ = self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(testMerchantUserAccount)
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

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_acknowlegde_order(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        _ = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(merchantUserAccount)
        p1 = self.createTestProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createTestProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        checkoutFormPayload = {
            "merchantId": str(merchant.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[1, 2]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        _ = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()

        # merchant should now acknowledge the order:
        acknowlegeOrderUrl = reverse("acknowledge_order_view", kwargs={"orderPk": order.pk}) 
        merchantAuthToken = self.loginAsMerchant()
        response = self.client.get(
            acknowlegeOrderUrl,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {merchantAuthToken}",
        )
        order = Order.objects.all().first()
        self.assertEqual(response.data["message"], "Order acknowledged successfully")
        self.assertTrue(order.acknowledged)
    
    def test_fulfill_order(self):
        pass


