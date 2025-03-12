from unittest.mock import patch
from django.apps import apps
from django.db import connection
from django.test import TestCase
import pytest
from rest_framework.reverse import reverse
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from django.core.mail import send_mail
from decimal import Decimal

from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderedProduct, record_cancellation
from global_test_config.global_test_config import (
    GlobalTestCaseConfig,
    MockedPaystackResponse,
)
from apps.transactions.models import Transaction
from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
from apps.products.models import GlobalProduct, BranchProduct

User = get_user_model()


@pytest.fixture(autouse=True)
def clean_database(db):
    """
    Automatically clean up the database before each test.
    """
    for model in apps.get_models():
        model.objects.all().delete()
    reset_auto_increment_ids()


def reset_auto_increment_ids():
    """
    Reset the auto-increment counter for all tables to 1.
    """
    with connection.cursor() as cursor:
        # Disable foreign key checks to avoid constraints errors during truncation
        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

        # For MySQL and PostgreSQL, reset sequences (auto-increment primary key counters)
        for model in apps.get_models():
            table_name = model._meta.db_table
            # Reset the auto-increment for MySQL and PostgreSQL
            cursor.execute(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1;")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")


# class OrderTests(GlobalTestCaseConfig, TestCase):

#     @patch(
#         "apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification"
#     )
#     @patch(
#         "apps.paystack.views.PaymentInitializationView.send_initiate_payment_request_to_paygate"
#     )
#     def test_create_order(self, mocked_response, mocked_send_notification):

#         mocked_response.return_value = MockedPaygateResponse()

#         customer = self.create_test_customer()
#         authToken = self.login_as_customer()
#         merchant_user_account = self.create_merchant_user_account()
#         merchant = self.create_merchant_business(merchant_user_account)
#         p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
#         p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
#         branch = merchant.branch_set.all().first()
#         checkout_form_payload = {
#             "branchId": str(merchant.pk),
#             "totalCheckoutAmount": "300.0",
#             "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
#             "discountTotal": "0",
#             "delivery": True,
#             "deliveryDate": self.make_date(1),
#             "address": "71 downthe street Bergville",
#         }
#         initiate_payment_url = reverse("initiate_payment_view")
#         _ = self.client.post(
#             initiate_payment_url,
#             data=checkout_form_payload,
#             HTTP_AUTHORIZATION=f"Token {authToken}",
#         )
#         paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
#         payment_notification_url = reverse("payment_notification_view")
#         response = self.client.post(
#             payment_notification_url,
#             data=paymentNotificationResponse,
#             content_type="application/x-www-form-urlencoded",
#         )
#         order = Order.objects.all().first()
#         products = order.transaction.products_ordered.filter(id__in=[p1.id, p2.id])
#         self.assertEqual(products[0].id, p1.id)
#         self.assertEqual(
#             order.transaction.branch.id, int(checkout_form_payload["branchId"])
#         )
#         self.assertEqual(order.status, Order.PENDING_DELIVERY)
#         self.assertEqual(order.transaction.customer.id, customer.id)

#     @patch(
#         "apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification"
#     )
#     @patch(
#         "apps.paystack.views.PaymentInitializationView.send_initiate_payment_request_to_paygate"
#     )
#     def test_get_all_orders_as_customer(
#         self, mocked_response, mocked_send_notification
#     ):

#         mocked_response.return_value = MockedPaygateResponse()

#         customer = self.create_test_customer()
#         customer_auth_token = self.login_as_customer()

#         merchant_user_account = self.create_merchant_user_account()
#         merchant = self.create_merchant_business(merchant_user_account)

#         p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
#         p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)

#         branch = merchant.branch_set.all().first()

#         checkout_form_payload = {
#             "branchId": str(branch.pk),
#             "totalCheckoutAmount": "300.0",
#             "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
#             "discountTotal": "0",
#             "delivery": True,
#             "deliveryDate": self.make_date(1),
#             "address": "71 downthe street Bergville",
#         }
#         initiate_payment_url = reverse("initiate_payment_view")
#         initiate_payment_response = self.client.post(
#             initiate_payment_url,
#             data=checkout_form_payload,
#             HTTP_AUTHORIZATION=f"Token {customer_auth_token}",
#         )

#         paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
#         payment_notification_url = reverse("payment_notification_view")
#         paymentNotificatonResponse = self.client.post(
#             payment_notification_url,
#             data=paymentNotificationResponse,
#             content_type="application/x-www-form-urlencoded",
#         )

#         getAllOrdersUrl = reverse("get_all_orders_view")
#         getAllOrdersResponse = self.client.get(
#             getAllOrdersUrl, HTTP_AUTHORIZATION=f"Token {customer_auth_token}"
#         )
#         order = Order.objects.all().first()
#         orderFromResponse = getAllOrdersResponse.data["orders"][0]
#         self.assertEqual(orderFromResponse["id"], order.id)
#         self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
#         self.assertEqual(
#             orderFromResponse["transaction"]["branch"]["id"],
#             int(checkout_form_payload["branchId"]),
#         )
#         self.assertEqual(
#             float(orderFromResponse["transaction"]["full_amount"]),
#             float(checkout_form_payload["totalCheckoutAmount"]),
#         )

#     @patch(
#         "apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification"
#     )
#     @patch(
#         "apps.paystack.views.PaymentInitializationView.send_initiate_payment_request_to_paygate"
#     )
#     def test_get_all_orders_as_merchant(
#         self, mocked_response, mocked_send_notification
#     ):

#         mocked_response.return_value = MockedPaygateResponse()

#         customer = self.create_test_customer()
#         customer_auth_token = self.login_as_customer()

#         merchant_user_account = self.create_merchant_user_account()
#         merchant = self.create_merchant_business(merchant_user_account)

#         p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
#         p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)

#         branch = merchant.branch_set.all().first()

#         checkout_form_payload = {
#             "branchId": str(branch.pk),
#             "totalCheckoutAmount": "300.0",
#             "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
#             "discountTotal": "0",
#             "delivery": True,
#             "deliveryDate": self.make_date(1),
#             "address": "71 down the street Bergville",
#         }
#         initiate_payment_url = reverse("initiate_payment_view")
#         initiate_payment_response = self.client.post(
#             initiate_payment_url,
#             data=checkout_form_payload,
#             HTTP_AUTHORIZATION=f"Token {customer_auth_token}",
#         )

#         payment_notification_response = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
#         payment_notification_url = reverse("payment_notification_view")
#         _ = self.client.post(
#             payment_notification_url,
#             data=payment_notification_response,
#             content_type="application/x-www-form-urlencoded",
#         )

#         merchant_auth_token = self.login_as_merchant()

#         get_all_orders_url = reverse("get_all_orders_view")
#         get_all_orders_response = self.client.get(
#             get_all_orders_url, HTTP_AUTHORIZATION=f"Token {merchant_auth_token}"
#         )
#         order = Order.objects.all().first()
#         order_from_response = get_all_orders_response.data["orders"][0]
#         self.assertEqual(order_from_response["id"], order.id)
#         self.assertEqual(order_from_response["transaction"]["id"], order.transaction.id)
#         self.assertEqual(
#             order_from_response["transaction"]["branch"]["id"],
#             int(checkout_form_payload["branchId"]),
#         )
#         self.assertEqual(
#             float(order_from_response["transaction"]["full_amount"]),
#             float(checkout_form_payload["totalCheckoutAmount"]),
#         )


class CancelOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer_user = User.objects.create_user(
            username="test_customer",
            email="customer@example.com",
            password="testpassword123",
        )
        self.customer_account = UserAccount.objects.create(
            user=self.customer_user,
            phone_number=1234567890,
            device_token="test_device_token_1",
            is_merchant=True,
        )

        self.another_customer_user = User.objects.create_user(
            username="another_customer",
            email="another_customer@example.com",
            password="testpassword123",
        )
        self.another_customer_account = UserAccount.objects.create(
            user=self.another_customer_user,
            phone_number=1276543210,
            device_token="test_device_token_2",
            is_merchant=True,
        )

        self.merchant_user = User.objects.create_user(
            username="merchant",
            email="merchant@example.com",
            password="merchantpassword123",
        )
        self.merchant_account = UserAccount.objects.create(
            user=self.merchant_user,
            phone_number=1255555555,
            device_token="merchant_device_token",
            is_merchant=True,
        )

        self.merchant_business = MerchantBusiness.objects.create(
            user_account=self.merchant_account,
            name="Test Merchant Business",
            email="merchant@example.com",
            delivery_fee="20.00",
        )

        self.branch = Branch.objects.create(
            merchant=self.merchant_business,
            address="123 Test St",
            area="Test Area",
            is_active=True,
        )

        self.customer_transaction = Transaction.objects.create(
            customer=self.customer_account, branch=self.branch
        )

        self.pending_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.PENDING_DELIVERY,
            acknowledged=True,
            delivery_fee=self.merchant_business.delivery_fee,
        )

        self.cancelled_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.CANCELLED,
            acknowledged=False,
            delivery_fee=self.merchant_business.delivery_fee,
        )

        self.delivered_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.DELIVERED,
            acknowledged=True,
            delivery_fee=self.merchant_business.delivery_fee,
        )

        self.pending_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.PENDING_DELIVERY,
            acknowledged=True,
            delivery_fee=self.merchant_business.delivery_fee,
        )

        self.cancel_order_url = reverse(
            "cancel_order", kwargs={"order_id": self.pending_order.id}
        )

    def _authenticate_customer(self, user=None):
        user = user or self.customer_user
        self.client.force_authenticate(user=user)

    def test_cancel_order_success(self):
        self._authenticate_customer()

        payload = {"order_id": self.pending_order.id}
        response = self.client.get(self.cancel_order_url)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Order cancelled successfully!")

    def test_cancel_order_unauthenticated(self):
        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_order_different_customer(self):
        self._authenticate_customer(user=self.another_customer_user)

        payload = {"order_id": self.pending_order.id}
        response = self.client.get(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_order_missing_order_id(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse("cancel_order", kwargs={"order_id": 0})

        response = self.client.get(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get("success", False))
        self.assertEqual(response.data.get("message"), "Order ID is required!")

    def test_cancel_order_invalid_order_id(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse("cancel_order", kwargs={"order_id": 99999})
        response = self.client.get(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_already_cancelled_order(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel_order", kwargs={"order_id": self.cancelled_order.pk}
        )
        response = self.client.get(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get("success", False))
        self.assertEqual(
            response.data.get("message"), "Order cannot be cancelled at this stage."
        )

    def test_cancel_delivered_order(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel_order", kwargs={"order_id": self.delivered_order.pk}
        )
        response = self.client.get(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get("success", False))
        self.assertEqual(
            response.data.get("message"), "Order cannot be cancelled at this stage."
        )

    def test_record_cancellation_creation(self):
        """Test basic cancellation record creation"""
        cancelled_order = record_cancellation(
            order=self.pending_order,
            user_account=self.customer_account,
            reason="CUSTOMER_REQUEST",
            notes="Test cancellation",
            refund_amount=Decimal("100.00"),
        )

        self.assertEqual(cancelled_order.order, self.pending_order)
        self.assertEqual(cancelled_order.cancelled_by, self.customer_account)
        self.assertEqual(cancelled_order.reason, "CUSTOMER_REQUEST")
        self.assertEqual(cancelled_order.additional_notes, "Test cancellation")
        self.assertEqual(cancelled_order.refund_amount, Decimal("100.00"))
        self.assertTrue(cancelled_order.refund_initiated)

