
from rest_framework.reverse import reverse

from apps.merchants.models import Branch
from global_test_config.global_test_config import GlobalTestCaseConfig


class MerchantDashboardTestCase(GlobalTestCaseConfig):

    def test_manage_branch_initial_dashboard(self):
        pass