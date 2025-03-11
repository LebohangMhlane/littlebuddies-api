from datetime import datetime
from decimal import ROUND_DOWN, Decimal
import json
from django.urls import reverse
import requests

from apps.orders.models import Order
from apps.paystack.models import Payment
from apps.transactions.models import Transaction
from global_test_config.global_test_config import GlobalTestCaseConfig


class TestPaystack(GlobalTestCaseConfig):

    def test_payment_model(self):
        pass

    def test_initialize_payment_view_success(self):

        # first get the url we will use to initialize the payment process:
        paystack_initialize_payment_url = reverse("initialize_payment")

        # create the checkout payload:
        order_data = {
            "amount": "195.00",  # Convert to kobo (or cents)
            "ordered_products": [1, 2, 3, 3],
            "branch": 1,
            "is_delivery": True,
            "delivery_date": datetime.today(),
            "delivery_address": "34 Blue Lagoon Street Offsprings"
        }

        # send the request to our server to start the payment process:
        response = self.client.post(
            paystack_initialize_payment_url,
            data=order_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.user_token}"
        )

        # check the transaction:
        transaction = Transaction.objects.all()[0]
        self.assertEqual(transaction.status, "PENDING")
        decimal_value = Decimal(transaction.total_with_service_fee).quantize(Decimal("0.00"), rounding=ROUND_DOWN)
        self.assertEqual(str(decimal_value), order_data["amount"])

        # check the payment:
        payment = Payment.objects.all()[0]
        self.assertEqual(payment.email, self.customer_user_account.user.email)
        self.assertFalse(payment.paid)
        self.assertEqual(str(payment.amount), order_data["amount"])
        self.assertEqual(payment.reference, transaction.reference)

        # check payment is attached to transaction:
        self.assertEqual(transaction.payment, payment)

        # check the order:
        order = Order.objects.all()[0]
        self.assertEqual(order.status, "PAYMENT_PENDING")
        self.assertEqual(order.delivery, True)
        self.assertEqual(str(order.delivery_fee), "20.00")
        self.assertEqual(order.transaction, transaction)

        # check the response data:
        response_data = response.json()
        self.assertEqual(response_data["success"], True)
        self.assertTrue("payment_url" in response_data)
        self.assertEqual(
            response_data["message"], "Payment initialized successfully!"
        )

    def test_verify_payment_view(self):
        pass
