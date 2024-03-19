from django.test import TestCase
from rest_framework.reverse import reverse

from apps.transactions.models import Transaction
from global_test_config.global_test_config import GlobalTestCaseConfig


class PayGateTests(GlobalTestCaseConfig, TestCase):

    def test_initiate_payment(self):

        testUserAccountLoginToken = self.createNormalTestAccountAndLogin()
        merchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(merchantUserAccount)
        _ = self.createTestProduct(merchant, merchantUserAccount, "Bob's dog food")
        _ = self.createTestProduct(merchant, merchantUserAccount, name="Bob's cat food")

        checkoutFormData = {
            "merchantId": str(merchant.pk),
            "totalCheckoutAmount": "1000",
            "items": "[1, 2]",
            "discountTotal": "0",
        }

        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormData,
            HTTP_AUTHORIZATION=f"Token {testUserAccountLoginToken}",
        )

        transaction = Transaction.objects.get(id=response.data["transaction"]["id"])
        
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.amount == int(checkoutFormData["totalCheckoutAmount"]))
        self.assertEqual(response.data["message"], "Paygate response was successful")
        self.assertEqual(response.data["paygatePayload"]["PAYGATE_ID"], "10011072130")
        self.assertEqual(response.data["transaction"]["productsPurchased"][0]["name"], "Bob's dog food" )
        self.assertEqual(response.data["transaction"]["productsPurchased"][1]["name"], "Bob's cat food" )

