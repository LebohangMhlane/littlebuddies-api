from django.urls import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class CancelOrderTests(GlobalTestCaseConfig):

    def test_app_manager_retrieval(self, user=None):
        get_app_manager_url = reverse("get_app_manager")
        response = self.client.get(
            get_app_manager_url, HTTP_AUTHORIZATION=f"Token {self.user_token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["data"]["maintenance_mode_on"], False)
