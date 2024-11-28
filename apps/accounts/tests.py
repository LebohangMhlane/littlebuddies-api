from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APIClient
import json

from apps.accounts.models import AccountSetting, UserAccount
from global_test_config.global_test_config import GlobalTestCaseConfig


class AccountsTests(GlobalTestCaseConfig, TestCase):

    def test_create_account(self):
        create_account_url = reverse("create_account_view")
        userInputData = {
            "username": "LebohangMhlane0621837747",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "asandamhlane@gmail.com",
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
            "email": "asandamhlane@gmail.com",
            "password": "HelloWorld",
        }
        response = self.create_normal_test_account()
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
        authToken = self.create_normal_test_account_and_login()
        getOrdersUrl = reverse("get_all_orders_view")
        response = self.client.get(
            path=getOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_navigation(self):
        self.create_normal_test_account_and_login()
        getOrdersUrl = reverse("get_all_orders_view")
        response = self.client.get(
            path=getOrdersUrl,
        )
        self.assertEqual(response.status_code, 401)

    def test_update_account(self):
        authToken = self.create_normal_test_account_and_login()
        updateAccountUrl = reverse("update_account_view")
        payload = {
            "phoneNumber": "0733084465"
        }
        self.assertTrue(payload["phoneNumber"] != self.userAccount.phone_number)
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
        authToken = self.create_normal_test_account_and_login()
        deactivateAccountUrl = reverse("deactivate_account_view")
        response = self.client.get(
            deactivateAccountUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        self.assertEqual(response.data["message"], "Account deactivated successfully")
        userAccount = UserAccount.objects.get(pk=self.userAccount.pk)
        self.assertTrue(userAccount.is_active == False)
        self.assertTrue(userAccount.user.is_active == False)

    def test_password_reset(self):
        accountToken = self.create_normal_test_account_and_login()
        resetPasswordUrl = reverse("password_reset_request_view", 
            kwargs={"email": "asandamhlane@gmail.com"})
        response = self.client.get(
            resetPasswordUrl,
            headers={'Authorization': f"Token {self.authToken}"}
        )


class AccountSettingsTestCase(GlobalTestCaseConfig, TestCase):

    def test_get_account_settings(self):

        auth_token = self.create_normal_test_account_and_login()

        _ = self.create_merchant_business(self.userAccount)

        account_settings_url = reverse("account_settings_view")
        response = self.client.get(
            account_settings_url, HTTP_AUTHORIZATION=f"Token {auth_token}"
        )

        account_settings = AccountSetting.objects.all()[0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(
            response.data["account_settings"]["full_name"], account_settings.full_name
        )

    def test_update_account_settings(self):
        pass

class DataRequestTestCase(GlobalTestCaseConfig, TestCase):

    def setUp(self):
        return super().setUp()
    
    def test_request_data_copy(self):

        auth_token = self.create_normal_test_account_and_login()
        
        url = reverse("request_data_copy")
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Token {auth_token}")
        pass

class UpdateAddressViewTests(TestCase):
    def setUp(self):
        create_account_url = reverse("create_account_view")
        
        self.userInputData = {
            "username": "EnzoLunga0813492640",
            "password": "King@2249",
            "firstName": "Enzo",
            "lastName": "Lunga",
            "email": "enzo@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0797281293",
            "deviceToken": "fidfjowehfoewfhowvehwoueh394e",
            "isMerchant": False,
        }

        self.client = APIClient()
        response = self.client.post(
            path=create_account_url,
            data=self.userInputData,
            format='json'
        )
        
        user_id = response.data['userAccount']['user']['id']
        self.user = User.objects.get(id=user_id)
        self.user_account = UserAccount.objects.get(id=response.data['userAccount']['id'])
        
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.update_address_url = reverse("update-address") 

    def test_update_address_successful(self):
        payload = {"address": "123 New Address, City"}
        
        response = self.client.patch(
            self.update_address_url,
            data=payload,
            format='json'
        )
        
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Address updated successfully")
        
        self.user_account.refresh_from_db()
        self.assertEqual(self.user_account.address, payload["address"])

    def test_update_address_unauthorized(self):
        self.client.credentials() 
        payload = {"address": "456 Unauthorized Address"}
        response = self.client.patch(
            self.update_address_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_address_invalid_data(self):
        """Test address update with invalid data."""
        payload = {"address": ""}  # Invalid as address is required
        response = self.client.patch(
            self.update_address_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid data provided")
        self.assertIn("errors", response.data)

    def test_update_address_wrong_data_format(self):
        payload = {"wrong_field": "123 New Address"}
        response = self.client.patch(
            self.update_address_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_user_account_not_found(self):
        self.user_account.delete()
        
        payload = {"address": "123 New Address"}
        response = self.client.patch(
            self.update_address_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])