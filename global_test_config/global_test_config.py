

from django.test import TestCase
from rest_framework.reverse import reverse


class GlobalTestCaseConfig(TestCase):

    def setUp(self) -> None:
        pass
        
    def createTestAccount(self):
        userInputData = {
            "username": "Lebo",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebohang@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0621837747",
            "isMerchant": False,
        }
        create_account_url = reverse("create_account_view")
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        return response.data
    
    def createTestAccountAndLogin(self):
        self.createTestAccount()
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
        self.authToken = response.data["token"]
        return self.authToken
