
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class MerchantDashboardTestCase(GlobalTestCaseConfig):

    def test_get_initial_dashboard(self):

        # sign in as a user:
        merchant_business = self.create_merchant_business()

        # set the url:
        url = reverse("get_merchant_dashboard")

        # make a get request to get the orders:
        response = self.client.get(url)

        pass
