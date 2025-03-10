from datetime import datetime
import json
from django.urls import reverse
import requests

from apps.paystack.models import Payment
from apps.transactions.models import Transaction
from global_test_config.global_test_config import GlobalTestCaseConfig


class TestPaystack(GlobalTestCaseConfig):

    def test_payment_model(self):
        pass

    def test_initialize_payment_view_success(self):

        # first get the url we will use to initialize the payment process:
        paystack_initialize_payment_url = reverse("initialize_payment")

        # set the checkout payload:
        order_data = {
            "amount": "499.99",  # Convert to kobo (or cents)
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

        # if something went wrong:
        if response.status_code != 201:
            response_data = response.json()
            raise Exception(f"Failed to initialize payment: {response_data['message']}")

        # do checks if things went well:
        else:
            # check the transaction:
            transaction = Transaction.objects.all()[0]
            self.assertEqual(transaction.status, "PENDING")
            self.assertEqual(transaction.total_with_service_fee, order_data["amount"])

            # check the payment:
            payment = Payment.objects.all()[0]
            self.assertEqual(payment.email, self.customer_user_account.user.email)
            self.assertFalse(payment.paid)
            self.assertEqual(str(payment.amount), order_data["amount"])
            self.assertEqual(payment.reference, transaction.reference)

            # check the response data:
            response_data = response.json()
            self.assertEqual(response_data["success"], True)
            self.assertTrue("payment_url" in response_data)
            self.assertEqual(
                response_data["message"], "Payment initialized successfully!"
            )

    def test_verify_payment_view(self):
        pass
