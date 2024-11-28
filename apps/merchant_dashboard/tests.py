
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class MerchantDashboardTestCase(GlobalTestCaseConfig):

    def test_get_initial_dashboard(self):

        # set the url:
        url = reverse("get_merchant_dashboard")

        pass
