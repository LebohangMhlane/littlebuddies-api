

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.reverse import reverse

from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness
from apps.products.models import Product


# test functions shared by all tests

class MockedPaygateResponse():

    status_code = 200
    text = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&CHECKSUM=b41a77f83a275a849f23e30b4666e837"

class GlobalTestCaseConfig(TestCase):

    def setUp(self) -> None:
        self.loginPayload = {
            "username": "Lebo",
            "password": "HelloWorld",
        }
        
    def createTestAdminAccount(self):
        userInputData = {
            "username": "Lebo",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebohang@gmail.com",
            "address": "71 rethman street newgermany",
            "phoneNumber": "0621837747",
            "isMerchant": False,
            "deviceToken": "fhewofhew89f394ry34f7g4f"
        }
        create_account_url = reverse("create_account_view")
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        testUserAccount = UserAccount.objects.get(
            user__username=userInputData["username"]
        )
        return testUserAccount
    
    def createTestCustomer(self):
        userInputData = {
            "username": "customer",
            "password": "HelloWorld",
            "firstName": "Customer",
            "lastName": "IWantToOrder",
            "email": "customer@gmail.com",
            "address": "21 everywhere street, The world",
            "phoneNumber": "0631837747",
            "isMerchant": False,
            "deviceToken": "cqmGKjazRUS5HfJypYk6r6:APA91bG0D4HYDz-21j2rK3mKP-M7HOAhcxR1_XEDCXUMqB4V_9Jd_1WFIAHq_zIw1o5LTPJUxJk4Xskzd4F1dO_OSk_bx4l48Jcac_KeXbGv5Fwj0aDZ-4-YsTEBvZei3t0dRgmw3yz0",
            "phoneNumberVerified": True,
        }
        customer = User.objects.create(
            username=userInputData["username"],
            password=make_password(userInputData["password"]),
            first_name=userInputData["firstName"],
            last_name=userInputData["lastName"],
            email=userInputData["email"],
        )
        testUserAccount = UserAccount.objects.create(
            user=customer,
            address=userInputData["address"],
            phoneNumber=userInputData["phoneNumber"],
            isMerchant=userInputData["isMerchant"],
            deviceToken=userInputData["deviceToken"],
            phoneNumberVerified=userInputData["phoneNumberVerified"]
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
            "phoneNumber": "0631837737",
            "isMerchant": True,
            "deviceToken": "fhwefhf2h3f9we7yfwefy32"
        }
        create_account_url = reverse("create_account_view")
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        testMerchantUserAccount = UserAccount.objects.get(user__username=userInputData["username"])
        return testMerchantUserAccount
    
    def createNormalTestAccountAndLogin(self):
        userAccount = self.createTestAdminAccount()
        loginUrl = reverse("login")
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=self.loginPayload,
        )
        self.authToken = response.data["token"]
        self.userAccount = userAccount
        return self.authToken

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
        return self.authToken

    def loginAsCustomer(self):
        loginUrl = reverse("login")
        loginPayload = {
            "username": "customer",
            "password": "HelloWorld",
        }
        response = self.client.post(
            loginUrl,
            data=loginPayload
        )
        self.authToken = response.data["token"]
        return self.authToken

    def loginAsSuperAdmin(self):
        pass

    def createTestMerchantBusiness(self, userAccount:UserAccount):
        merchant = MerchantBusiness.objects.create(
            userAccount=userAccount,
            name="Pet Food Shop",
            email="petfoodshop@gmail.com",
            address="12 Pet Street Newgermany",
            paygateReference="pgtest_123456789",
            paygateId="10011072130",
            paygateSecret="secret"
        )
        return merchant

    def makeUserAccountSuperAdmin(self, userAccountPk:int):
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        userAccount.user.is_superuser = True
        userAccount.user.save()
        userAccount.canCreateMerchants = True
        userAccount.save()
        return userAccount

    def createTestProduct(self, merchant, merchantUserAccount, name, price, discountPercent=0):
        product = Product.objects.create(
            merchant=merchant,
            name=name,
            description="High quality dog food",
            originalPrice=price,
            image="image",
            inStock=True,
            storeReference="ID2342",
            discountPercentage=discountPercent,
            createdBy=merchantUserAccount,
            isActive=True,
        )
        return product
    