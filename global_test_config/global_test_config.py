

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch, MerchantBusiness, SaleCampaign
from apps.products.models import BranchProduct, Product


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
    
    def createTestMerchantUserAccount(self, userData={}):
        try:
            fakeUserData = {
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
            _ = self.client.post(
                path=create_account_url,
                content_type=f"application/json",
                data=fakeUserData if len(userData) == 0 else userData,
            )
            merchantUserAccount = UserAccount.objects.get(
                user__email=fakeUserData["email"] if len(userData) == 0 else userData["email"]
            )
            merchantUserAccount.isMerchant = True
            merchantUserAccount.save()
            return merchantUserAccount
        except Exception as e:
            pass
    
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
    
    def makeUserAccountAMerchant(self, userAccount:UserAccount) -> UserAccount:
        userAccount.isMerchant = True
        userAccount.save()
        return userAccount

    def createTestMerchantBusiness(self, userAccount:UserAccount, merchantData={}):
        userAccount = self.makeUserAccountAMerchant(userAccount)
        try:
            merchant = MerchantBusiness()
            if len(merchantData) == 0:
                merchant.userAccount = userAccount
                merchant.name="Absolute Pets"
                merchant.email="absolutepets@gmail.com"
                merchant.address="Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640"
                merchant.paygateReference="pgtest_123456789"
                merchant.paygateId="10011072130"
                merchant.paygateSecret="secret"
                merchant.setBranchAreas(["New Germany", "Durban Central"])
                merchant.save()
            else:
                merchant.userAccount=userAccount
                merchant.name=merchantData["name"]
                merchant.email=merchantData["email"]
                merchant.address=merchantData["address"]
                merchant.paygateReference="pgtest_123456789"
                merchant.paygateId=merchantData["paygateId"]
                merchant.paygateSecret=merchantData["paygateSecret"]
                merchant.setBranchAreas(merchantData["branchAreas"])
                merchant.save()
        except Exception as e:
            pass
        try:
            branch1 = Branch()
            if len(merchantData) == 0:
                branch1.isActive=True
                branch1.address = "Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640"
                branch1.merchant = merchant
                branch1.area = "New Germany"
                branch1.save()

            branch2 = Branch()
            if len(merchantData) == 0:
                branch2.isActive=True
                branch2.address = "Shop 116A, Musgrave Centre, 115 Musgrave Rd, Berea, Durban, 4001"
                branch2.merchant = merchant
                branch2.area = "Durban Central"
                branch2.save()

            else:
                branch1.isActive=True
                branch1.address = merchantData["address"]
                branch1.merchant = merchant
                branch1.area = merchantData["branchAreas"][0]
                branch1.save()
        except Exception as e:
            pass
        return merchant
    
    def makeNormalAccountSuperAdmin(self, userAccountPk:int):
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        userAccount.user.is_superuser = True
        userAccount.user.save()
        userAccount.canCreateMerchants = True
        userAccount.save()
        return userAccount

    def createTestProduct(self, merchant:MerchantBusiness, merchantUserAccount, name, price, discountPercent=0):
        try:
            branches = Branch.objects.filter(merchant=merchant)

            product, bool = Product.objects.get_or_create(
                name=name,
                description="High quality dog food",
                recommendedRetailPrice=300,
                image="image",
                category=1
            )

            for branch in branches:
                branchProduct = BranchProduct()
                branchProduct.branch = branch
                branchProduct.branchPrice = product.recommendedRetailPrice + price # store charging R100 more
                branchProduct.storeReference = "3EERDE2"
                branchProduct.createdBy = merchantUserAccount
                branchProduct.product = product
                branchProduct.save()

                if discountPercent > 0:
                    saleCampaign = SaleCampaign()
                    saleCampaign.branch = branch
                    saleCampaign.campaignEnds = datetime.now() + timedelta(days=5)
                    saleCampaign.percentageOff = discountPercent
                    saleCampaign.save()
                    saleCampaign.branchProducts.add(branchProduct)
                    saleCampaign.save()

        except Exception as e:
            pass
        return branchProduct
    
    def makeDate(self, daysFromNow):
        date = datetime.now() + timedelta(days=daysFromNow)
        date = date.strftime("%d %B %Y")
        return date