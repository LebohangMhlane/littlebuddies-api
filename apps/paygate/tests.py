from django.test import TestCase
from rest_framework.reverse import reverse

from unittest.mock import patch
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse

from apps.orders.models import Order
from apps.transactions.models import Transaction


class PayGateTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_initiate_payment_as_customer_full_price(self, mockedResponse):

        mockedResponse.return_value = MockedPaygateResponse()

        testCustomer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)
        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        branch = merchant.branch_set.all().first()
        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "400.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.amount == checkoutFormPayload["totalCheckoutAmount"])
        self.assertEqual(response.data["message"], "Paygate response was successful")
        self.assertEqual(response.data["paygatePayload"]["PAYGATE_ID"], "10011072130")
        self.assertEqual(response.data["transaction"]["productsPurchased"][0]["branchProduct"]["product"], 1)
        self.assertEqual(response.data["transaction"]["productsPurchased"][1]["branchProduct"]["product"], 2)
        self.assertEqual(response.data["transaction"]["productsPurchased"][1]["quantityOrdered"], 2)
        self.assertEqual(response.data["transaction"]["customer"]["address"], testCustomer.address)

    
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_check_transaction_status(self, mockedResponse):

        mockedResponse.return_value = MockedPaygateResponse()

        createTestCustomer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)
        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        branch = merchant.branch_set.first()
        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "400.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        transaction.status = transaction.COMPLETED
        transaction.save()
        reference = transaction.reference

        # test begins:
        checkTransactionStatusUrl = reverse("check_transaction_status", args=[reference])
        response = self.client.get(
            checkTransactionStatusUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.data["message"], f"Transaction {reference} status retrieved successfully")
        self.assertEqual(response.data["transactionStatus"], transaction.COMPLETED)
    

    # @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_paygate_notification(self, mockedResponse):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)
        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        branch = merchant.branch_set.first()
        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
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
        self.assertEqual(order.transaction.branch.id, int(checkoutFormPayload["branchId"]))
        self.assertEqual(order.status, Order.PENDING_DELIVERY)
        self.assertEqual(order.transaction.status, Transaction.COMPLETED)
        self.assertEqual(order.transaction.customer.id, customer.id)


