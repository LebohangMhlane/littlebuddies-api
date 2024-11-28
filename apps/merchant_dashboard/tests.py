
from rest_framework.reverse import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class MerchantDashboardTestCase(GlobalTestCaseConfig):

    def test_get_initial_dashboard(self):

        # create a merchant user account:
        merchant_user_account = self.create_merchant_user_account()
        
        # create a merchant business:
        merchant_business = self.create_merchant_business(merchant_user_account)

        # create a 2nd branch:
        second_branch = self.create_a_branch(merchant_business)

        # sign in as a merchant:
        token = self.login_as_merchant()

        # set the url:
        url = reverse("get_merchant_dashboard", kwargs={"branch_id": 1})

        # make a get request to get the orders:
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Token {token}"
        )

        # assertions:
        self.assertEqual(response.status_code, 200)
