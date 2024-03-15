

from django.test import TestCase
from rest_framework.reverse import reverse

from accounts.models import UserAccount


class GlobalTestCaseConfig(TestCase):

    def setUp(self) -> None:

        self.userInputData = {
            "username": "Lebo",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebohang@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0621837747",
            "isMerchant": False,
        }
        
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
        userAccount = UserAccount.objects.get(user__username=loginPayload["username"])
        self.userAccount = userAccount
        return self.authToken

    def createTestMerchant(self):
        createMerchantPayload = {
            "userAccountPk": 1,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.createTestAccountAndLogin()
        self.makeUserAccountFullAdmin(createMerchantPayload["userAccountPk"])
        createMerchantUrl = reverse("create_merchant_view")
        self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )

    def makeUserAccountFullAdmin(self, userAccountPk:int):
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        userAccount.user.is_superuser = True
        userAccount.user.save()
        userAccount.can_create_merchants = True
        userAccount.save()

    