from django.test import TestCase

from rest_framework.reverse import reverse

from unittest.mock import patch

from apps.orders.models import Order
from apps.transactions.models import Transaction

from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse

class PayGateTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_initiate_payment_as_customer_full_price(self, mockedResponse):

        mockedResponse.return_value = MockedPaygateResponse()

        createTestCustomer = self.createTestCustomer()
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
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.amount == float(checkoutFormPayload["totalCheckoutAmount"]))
        self.assertEqual(response.data["message"], "Paygate response was successful")
        self.assertEqual(response.data["paygatePayload"]["PAYGATE_ID"], "10011072130")
        self.assertEqual(response.data["transaction"]["productsPurchased"][0]["name"], "Bob's dog food")
        self.assertEqual(response.data["transaction"]["productsPurchased"][1]["name"], "Bob's cat food")
        self.assertEqual(response.data["transaction"]["customer"]["address"], createTestCustomer.address)

    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_initiate_payment_as_customer_discounted(self, mockedResponse):

        mockedResponse.status_code = 200
        mockedResponse.return_value = MockedPaygateResponse()

        createTestCustomer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(merchantUserAccount)
        p1 = self.createTestProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createTestProduct(merchant, merchantUserAccount, "Bob's cat food", 100, 50)
        checkoutFormPayload = {
            "merchantId": str(merchant.pk),
            "totalCheckoutAmount": "250.0",
            "products": "[1, 2]",
            "discountTotal": "50",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.amount == float(checkoutFormPayload["totalCheckoutAmount"]))
        self.assertEqual(response.data["message"], "Paygate response was successful")
        self.assertEqual(response.data["paygatePayload"]["PAYGATE_ID"], "10011072130")
        self.assertEqual(response.data["transaction"]["productsPurchased"][0]["name"], "Bob's dog food")
        self.assertEqual(response.data["transaction"]["productsPurchased"][1]["name"], "Bob's cat food")
        self.assertEqual(response.data["transaction"]["customer"]["address"], createTestCustomer.address)

    @patch("apps.integrations.firebase_instance.firebase_instance_module.FirebaseInstance.FirebaseInstance.sendNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_paygate_notification(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
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
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        response = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()
        products = order.transaction.productsPurchased.filter(id__in=[p1.id, p2.id])
        self.assertEqual(products[0].id, p1.id)
        self.assertEqual(products[1].id, p2.id)
        self.assertEqual(order.transaction.merchant.id, int(checkoutFormPayload["merchantId"]))
        self.assertEqual(order.status, "PENDING")
        self.assertEqual(order.transaction.customer.id, customer.id)


