from django.test import TestCase
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class PayGateTests(GlobalTestCaseConfig, TestCase):

    def test_initiate_payment(self):

        testUserAccountLoginToken = self.createTestAccountAndLogin()
        merchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchant(merchantUserAccount)

        checkoutFormPayload = {
            "merchantId": str(merchant.pk),
            "totalCheckoutAmount": "1000",
            "items": "[1, 3]",
        }

        initiate_payment_url = reverse("initiate_payment_view")
        response = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {testUserAccountLoginToken}",
        )
