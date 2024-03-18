

from django.test import TestCase
from rest_framework.reverse import reverse

from apps.accounts.models import UserAccount
from apps.merchants.models import Merchant, Product


# test functions shared by all tests

class GlobalTestCaseConfig(TestCase):

    def setUp(self) -> None:
        self.loginPayload = {
            "username": "Lebo",
            "password": "HelloWorld",
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
        self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        testUserAccount = UserAccount.objects.get(
            user__username=userInputData["username"]
        )
        return testUserAccount
    
    def createTestMerchantUserAccount(self):
        userInputData = {
            "username": "Mike",
            "password": "HelloWorld",
            "firstName": "Mike",
            "lastName": "Myers",
            "email": "mikemyers@gmail.com",
            "address": "72 rethman street newgermany",
            "phoneNumber": "0631837747",
            "isMerchant": True,
        }
        create_account_url = reverse("create_account_view")
        self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        testMerchantUserAccount = UserAccount.objects.get(
            user__username=userInputData["username"]
        )
        return testMerchantUserAccount
    
    def createTestAccountAndLogin(self):
        userAccount = self.createTestAccount()
        loginUrl = reverse("login")
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=self.loginPayload,
        )
        self.authToken = response.data["token"]
        userAccount = UserAccount.objects.get(user__username=self.loginPayload["username"])
        self.userAccount = userAccount
        return self.authToken
    
    # TODO: complete login flavours

    def loginAsMerchant(self):
        loginUrl = reverse("login")
        loginPayload = {
            "username": "Mike",
            "password": "HelloWorld",
        }
        response = self.client.post(
            loginUrl,
            data=loginPayload
        )
        self.authToken = response.data["token"]

    def loginAsCustomer(self):
        pass

    def loginAsSuperAdmin(self):
        pass

    def createTestMerchant(self, userAccount:UserAccount):
        merchant = Merchant.objects.create(
            userAccount=userAccount,
            name="Pet Food Shop",
            email="petfoodshop@gmail.com",
            address="12 Pet Street Newgermany",
            paygateReference="pgtest_123456789",
            paygateId="10011072130",
            paygateSecret="secret"
        )
        return merchant

    def makeUserAccountFullAdmin(self, userAccountPk:int):
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        userAccount.user.is_superuser = True
        userAccount.user.save()
        userAccount.canCreateMerchants = True
        userAccount.save()
        return userAccount

    def createTestProduct(self, merchant):
        product = Product.objects.create(
            merchant=merchant,
            name="Bob's Dog Food",
            description="High quality dog food",
            originalPrice=450,
            image="image",
            inStock=True,
            storeReference="ID2342",
            discountPercentage=0,
        )
        return product
    