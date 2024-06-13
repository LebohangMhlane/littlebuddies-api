from unittest.mock import patch
from django.test import TestCase
from rest_framework.reverse import reverse

from apps.orders.models import Order
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse


class OrderTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_create_order(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)
        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        branch = merchant.branch_set.all().first()
        checkoutFormPayload = {
            "branchId": str(merchant.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
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
        self.assertEqual(order.transaction.customer.id, customer.id)


    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_get_all_orders_as_customer(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        customerAuthToken = self.loginAsCustomer()

        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)

        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiatePaymentResponse = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}",
        )

        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        paymentNotificatonResponse = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )

        getAllOrdersUrl = reverse("get_all_orders_view")
        getAllOrdersResponse = self.client.get(
            getAllOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}"
        )
        order = Order.objects.all().first()
        orderFromResponse = getAllOrdersResponse.data["orders"][0]
        self.assertEqual(
            orderFromResponse["id"], order.id
        )
        self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            orderFromResponse["transaction"]["branch"]["id"], 
            int(checkoutFormPayload["branchId"]))
        self.assertEqual(
            float(orderFromResponse["transaction"]["amount"]), 
            float(checkoutFormPayload["totalCheckoutAmount"])
        )


    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_get_all_orders_as_merchant(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        customerAuthToken = self.loginAsCustomer()

        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)

        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiatePaymentResponse = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}",
        )

        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        paymentNotificatonResponse = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )

        merchantAuthToken = self.loginAsMerchant()

        getAllOrdersUrl = reverse("get_all_orders_view")
        getAllOrdersResponse = self.client.get(
            getAllOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {merchantAuthToken}"
        )
        order = Order.objects.all().first()
        orderFromResponse = getAllOrdersResponse.data["orders"][0]
        self.assertEqual(
            orderFromResponse["id"], order.id
        )
        self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            orderFromResponse["transaction"]["branch"]["id"], 
            int(checkoutFormPayload["branchId"]))
        self.assertEqual(
            float(orderFromResponse["transaction"]["amount"]), 
            float(checkoutFormPayload["totalCheckoutAmount"])
        )