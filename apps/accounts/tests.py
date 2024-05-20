from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserAccount
from global_test_config.global_test_config import GlobalTestCaseConfig


class AccountsTests(GlobalTestCaseConfig, TestCase):

    def test_create_account(self):
        create_account_url = reverse("create_account_view")
        userInputData = {
            "username": "LebohangMhlane0621837747",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebohang@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0621837747",
            "deviceToken": "fidfjowehfoewfhowvehwoueh394e",
            "isMerchant": False,
        }
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        user = User.objects.get(username=response.data["userAccount"]["user"]["username"])
        userAccount = UserAccount.objects.get(pk=response.data["userAccount"]["id"])
        token = Token.objects.get(user=user)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(token != None)
        self.assertEqual(user.username, userInputData["username"])
        self.assertEqual(userAccount.user.username, userInputData["username"])

    def test_create_account_failure(self):
        userInputData = {
            "username": "LebohangMhlane0621837747",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebohang@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0621837747",
            "deviceToken": "fidfjowehfoewfhowvehwoueh394e",
            "isMerchant": False,
            "isSuperUser": False,
        }
        create_account_url = reverse("create_account_view")
        userInputData["phoneNumber"] = "062183774" # deliberate incorrect phone number
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        user = User.objects.all().first()
        userAccount = UserAccount.objects.all().first()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"], "Invalid phone number")
        self.assertEqual(user, None)
        self.assertEqual(userAccount, None)

    def test_log_in(self):
        userInputData = {
            "email": "lebohang@gmail.com",
            "password": "HelloWorld",
        }
        response = self.createNormalTestAccount()
        loginUrl = reverse("login")
        loginPayload = {
            "email": userInputData["email"],
            "password": userInputData["password"],
        }
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=loginPayload,
        )
        user = User.objects.get(email=userInputData["email"])
        token = Token.objects.get(user=user)
        tokenInResponse = response.data["token"]
        self.assertEqual(token.key, tokenInResponse)

    def test_authorized_navigation(self):
        authToken = self.createNormalTestAccountAndLogin()
        getOrdersUrl = reverse("get_all_orders_view")
        response = self.client.get(
            path=getOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_navigation(self):
        self.createNormalTestAccountAndLogin()
        getOrdersUrl = reverse("get_all_orders_view")
        response = self.client.get(
            path=getOrdersUrl,
        )
        self.assertEqual(response.status_code, 401)

    def test_update_account(self):
        authToken = self.createNormalTestAccountAndLogin()
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

    def test_deactivate_account(self):
        authToken = self.createNormalTestAccountAndLogin()
        deactivateAccountUrl = reverse("deactivate_account_view")
        response = self.client.get(
            deactivateAccountUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.data["message"], "Account deactivated successfully")
        userAccount = UserAccount.objects.get(pk=self.userAccount.pk)
        self.assertTrue(userAccount.isActive == False)
        self.assertTrue(userAccount.user.is_active == False)


