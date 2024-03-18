from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserAccount
from global_test_config.global_test_config import GlobalTestCaseConfig

class AccountsTests(GlobalTestCaseConfig, TestCase):

    def test_create_account(self):
        create_account_url = reverse("create_account_view")
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=self.userInputData,
        )
        user = User.objects.get(username=response.data["userAccount"]["user"]["username"])
        userAccount = UserAccount.objects.get(pk=response.data["userAccount"]["id"])
        token = Token.objects.get(user=user)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(token != None)
        self.assertEqual(user.username, self.userInputData["username"])
        self.assertEqual(userAccount.user.username, self.userInputData["username"])

    def test_create_account_failure(self):
        create_account_url = reverse("create_account_view")
        self.userInputData["phoneNumber"] = "062183774" # deliberate incorrect phone number
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=self.userInputData,
        )
        user = User.objects.all().first()
        userAccount = UserAccount.objects.all().first()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["exception"], "Invalid phone number")
        self.assertEqual(user, None)
        self.assertEqual(userAccount, None)

    def test_log_in(self):
        response = self.createTestAccount()
        loginUrl = reverse("login")
        loginPayload = {
            "username": self.userInputData["username"],
            "password": self.userInputData["password"],
        }
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=loginPayload,
        )
        user = User.objects.get(username=self.userInputData["username"])
        token = Token.objects.get(user=user)
        tokenInResponse = response.data["token"]
        self.assertEqual(token.key, tokenInResponse)

    def test_authorized_navigation(self):
        authToken = self.createTestAccountAndLogin()
        paymentsUrl = reverse("initiate_payment_view")
        response = self.client.get(
            path=paymentsUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_navigation(self):
        self.createTestAccountAndLogin()
        paymentsUrl = reverse("initiate_payment_view")
        response = self.client.get(
            path=paymentsUrl,
        )
        self.assertEqual(response.status_code, 401)

    def test_update_account(self):
        authToken = self.createTestAccountAndLogin()
        updateAccountUrl = reverse("update_account_view")
        payload = {
            "phoneNumber": "0733084465"
        }
        self.assertTrue(payload["phoneNumber"] != self.userAccount.phoneNumber)
        response = self.client.post(
            path=updateAccountUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        receivedPhoneNumber = f"0{response.data['updatedAccount']['phoneNumber']}"
        self.assertEqual(receivedPhoneNumber, 
            payload["phoneNumber"]
        )



