from django.test import TestCase
from rest_framework.reverse import reverse

# Create your tests here.


class PayGateTests(TestCase):

    def test_initiate_payment(self):

        initiate_payment_url = reverse("initiate_payment_view")
        
        response = self.client.post(
            initiate_payment_url,
        )

        print(initiate_payment_url)