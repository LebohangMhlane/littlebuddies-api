from django.apps import apps
from django.db import connection
from django.test import TestCase
import pytest
from rest_framework.reverse import reverse

from unittest.mock import patch
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse

from apps.orders.models import Order
from apps.transactions.models import Transaction


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


class PayGateTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_initiate_payment_as_customer_full_price(self, mocked_response):

        # fix this text case:

        mocked_response.return_value = MockedPaygateResponse()

        testCustomer = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant_business = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant_business, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant_business, merchant_user_account, "Bob's cat food", 100)
        branch = merchant_business.branch_set.all().first()
        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "400.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.make_date(1),
            "address": "71 downthe street Bergville",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.amount == checkout_form_payload["totalCheckoutAmount"])
        self.assertEqual(response.data["message"], "Paygate response was successful")
        self.assertEqual(response.data["paygate_payload"]["PAYGATE_ID"], "10011072130")
        self.assertEqual(response.data["transaction"]["products_purchased"][0]["branch_product"]["product"], 1)
        self.assertEqual(response.data["transaction"]["products_purchased"][1]["quantity_ordered"], 2)
        self.assertEqual(response.data["transaction"]["customer"]["address"], testCustomer.address)

    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_check_transaction_status(self, mocked_response):

        mocked_response.return_value = MockedPaygateResponse()

        createTestCustomer = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
        branch = merchant.branch_set.first()
        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "400.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.make_date(1),
            "address": "71 downthe street Bergville",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
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

    # @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_paygate_notification(self, mocked_response):

        mocked_response.return_value = MockedPaygateResponse()

        customer = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
        branch = merchant.branch_set.first()
        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        response = self.client.post(
            payment_notification_url,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()
        products = order.transaction.products_purchased.filter(id__in=[p1.id, p2.id]).all()
        self.assertEqual(products[0].id, p1.id)
        self.assertEqual(
            order.transaction.branch.id, int(checkout_form_payload["branchId"])
        )
        self.assertEqual(order.status, Order.PENDING_DELIVERY)
        self.assertEqual(order.transaction.status, Transaction.COMPLETED)
        self.assertEqual(order.transaction.customer.id, customer.id)
