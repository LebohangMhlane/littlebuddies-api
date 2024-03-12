from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.reverse import reverse

from accounts.models import UserAccount


class AccountsTests(TestCase):

    def setUp(self) -> None:
        
        self.user_input_data = {
            "username": "Lebo",
            "password": "HelloWorld",
            "first_name": "Lebohang",
            "last_name": "Mhlane",
            "email": "lebohang@gmail.com",
        }

    def test_create_account(self):

        create_account_url = reverse("create_account_view")

        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=self.user_input_data,
        )

        user = User.objects.all().first()
        user_account = UserAccount.objects.all().first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.username, self.user_input_data["username"])
        self.assertEqual(user_account.user.username, self.user_input_data["username"])



