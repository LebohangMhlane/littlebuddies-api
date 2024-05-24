

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness
from apps.products.models import Product


# test functions shared by all tests

class MockedPaygateResponse():

    status_code = 200
    text = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&CHECKSUM=b41a77f83a275a849f23e30b4666e837"

class GlobalTestCaseConfig(TestCase):

    # TODO: remember to clean up test cases and move all repetitive tasks here:

    def setUp(self) -> None:
        self.loginPayload = {
            "email": "lebohang@gmail.com",
            "password": "HelloWorld",
        }
        
    def createNormalTestAccount(self):
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
            user__username=response.data["userAccount"]["user"]["username"]
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
        token = Token.objects.create(user=customer)
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
        testMerchantUserAccount = UserAccount.objects.get(user__email=userInputData["email"])
        testMerchantUserAccount.isMerchant = True
        testMerchantUserAccount.save()
        return testMerchantUserAccount
    
    def createTestMerchantUserAccountDynamic(self, userData):
        userInputData = {
            "username": userData["username"],
            "password": userData["password"],
            "firstName": userData["firstName"],
            "lastName": userData["lastName"],
            "email": userData["email"],
            "address": userData["address"],
            "phoneNumber": userData["phoneNumber"],
            "isMerchant": userData["isMerchant"],
            "deviceToken": userData["deviceToken"]
        }
        create_account_url = reverse("create_account_view")
        response = self.client.post(
            path=create_account_url,
            content_type=f"application/json",
            data=userInputData,
        )
        testMerchantUserAccount = UserAccount.objects.get(user__email=userInputData["email"])
        return testMerchantUserAccount
    
    def createNormalTestAccountAndLogin(self):
        userAccount = self.createNormalTestAccount()
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
            "email": "mikemyers@gmail.com",
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
            "email": "customer@gmail.com",
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
    
    def makeUserAccountAMerchant(self, userAccount:UserAccount):
        userAccount.isMerchant = True
        userAccount.save()
        return userAccount

    def createTestMerchantBusiness(self, userAccount:UserAccount):
        userAccount = self.makeUserAccountAMerchant(userAccount)
        try:
            merchant = MerchantBusiness.objects.create(
                userAccount=userAccount,
                name="Absolute Pets",
                email="absolutepets@gmail.com",
                address="Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640",
                paygateReference="pgtest_123456789",
                paygateId="10011072130",
                paygateSecret="secret",
                area="New Germany",
                hasSpecials=False,
            )
        except Exception as e:
            pass
        return merchant
    
    def createTestMerchantBusinessDynamic(self, userAccount:UserAccount, businessData):
        userAccount = self.makeUserAccountAMerchant(userAccount)
        merchant = MerchantBusiness.objects.create(
            userAccount=userAccount,
            name=businessData["name"],
            email=businessData["email"],
            address=businessData["address"],
            paygateReference="pgtest_123456789",
            paygateId=businessData["paygateId"],
            paygateSecret=businessData["paygateSecret"],
            area=businessData["area"],
            hasSpecials=businessData["hasSpecials"],
        )
        return merchant

    def makeNormalAccountSuperAdmin(self, userAccountPk:int):
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
    
    def makeDate(self, daysFromNow):
        date = datetime.now() + timedelta(days=daysFromNow)
        date = date.strftime("%d %B %Y")
        return date