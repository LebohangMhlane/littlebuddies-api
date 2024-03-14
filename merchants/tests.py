from django.test import TestCase

from global_test_config.global_test_config import GlobalTestCaseConfig
from merchants.models import Merchant

# Create your tests here.


class MerchantTests(GlobalTestCaseConfig, TestCase):

    def test_create_merchant(self):

        self.createTestAccountAndLogin()
        
        # TODO: create a merchant using a made up form: