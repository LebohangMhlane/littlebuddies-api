from django.urls import reverse
import requests

from global_test_config.global_test_config import GlobalTestCaseConfig


class TestPaystack(GlobalTestCaseConfig):

    def test_payment_model(self):
        pass

    def test_initialize_payment_view_success(self):

        # first get the url we will use to initialize the payment process:
        paystack_initialize_payment_url = reverse("initialize_payment")

        # set the checkout payload:
        data = {
            "email": self.customer_user_account.user.email,
            "amount": "199.99",  # Convert to kobo (or cents)
            "reference": "paystack_test_reference",
        }

        # send the request to our server to start the payment process:
        response = self.client.post(
            paystack_initialize_payment_url, data=data
        )

        # if something went wrong:
        if response.status_code != 201:
            response_data = response.json()
            raise Exception(f"Failed to initialize payment: {response_data['message']}")

        # do checks if things went well:
        else:
            response_data = response.json()
            self.assertEqual(response_data["success"], True)
            self.assertTrue("payment_url" in response_data)
            self.assertEqual(
                response_data["message"], "Payment initialized successfully!"
            )


    def test_verify_payment_view(self):
        pass
