

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

    def create_branch_product(self, branch):
        pass

    def create_a_branch(self, merchant):
        
        # create a dummy branch:
        branch = Branch()
        branch.is_active = True
        branch.address = "12 down the road street, Durban, 3000"
        branch.merchant = merchant
        branch.area = "Westville"
        branch.save()

    def setUp(self) -> None:
        self.loginPayload = {
            "email": "asandamhlane@gmail.com",
            "password": "HelloWorld",
        }
        
    def create_normal_test_account(self):
        userInputData = {
            "username": "Lebo",
            "password": "HelloWorld",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "asandamhlane@gmail.com",
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
    
    def create_test_customer(self):
        userInputData = {
            "username": "customer",
            "password": "HelloWorld",
            "firstName": "Customer",
            "lastName": "IWantToOrder",
            "email": "customer@gmail.com",
            "address": "71 Rethman Street, New Germany, Durban",
            "phoneNumber": "0631837747",
            "isMerchant": False,
            "deviceToken": "cqmGKjazRUS5HfJypYk6r6:APA91bG0D4HYDz-21j2rK3mKP-M7HOAhcxR1_XEDCXUMqB4V_9Jd_1WFIAHq_zIw1o5LTPJUxJk4Xskzd4F1dO_OSk_bx4l48Jcac_KeXbGv5Fwj0aDZ-4-YsTEBvZei3t0dRgmw3yz0",
            "emailVerified": True,
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
            emailVerified=userInputData["emailVerified"],
        )
        token = Token.objects.create(user=customer)
        return testUserAccount
    
    def create_merchant_user_account(self, user_data={}):
        try:
            fake_user_data = {
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
                data=fake_user_data if len(user_data) == 0 else user_data,
            )
            merchant_user_account = UserAccount.objects.get(
                user__email=fake_user_data["email"] if len(user_data) == 0 else user_data["email"]
            )
            merchant_user_account.is_merchant = True
            merchant_user_account.save()
            return merchant_user_account
        except Exception as e:
            pass
    
    def create_dynamic_merchant_user_account(self, userData):
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
    
    def create_normal_test_account_and_login(self):
        userAccount = self.create_normal_test_account()
        loginUrl = reverse("login")
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=self.loginPayload,
        )
        self.authToken = response.data["token"]
        self.userAccount = userAccount
        return self.authToken

    def login_as_merchant(self):
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

    def login_as_customer(self):
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

    def login_as_super_admin(self):
        pass
    
    def make_user_account_a_merchant(self, user_account:UserAccount) -> UserAccount:
        user_account.is_merchant = True
        user_account.save()
        return user_account

    def create_merchant_business(self, user_account:UserAccount, merchant_data={}):
        user_account = self.make_user_account_a_merchant(user_account)
        try:
            merchant = MerchantBusiness()
            if len(merchant_data) == 0:
                merchant.user_account = user_account
                merchant.name="Absolute Pets"
                merchant.email="absolutepets@gmail.com"
                merchant.address="Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640"
                merchant.paygate_reference="pgtest_123456789"
                merchant.paygate_id="10011072130"
                merchant.paygate_secret="secret"
                merchant.set_branch_areas(["New Germany", "Durban Central"])
                merchant.save()
            else:
                merchant.user_account=user_account
                merchant.name=merchant_data["name"]
                merchant.email=merchant_data["email"]
                merchant.address=merchant_data["address"]
                merchant.paygate_reference="pgtest_123456789"
                merchant.paygate_id=merchant_data["paygateId"]
                merchant.paygate_secret=merchant_data["paygateSecret"]
                merchant.set_branch_areas(merchant_data["branchAreas"])
                merchant.save()
        except Exception as e:
            pass
        try:
            branch1 = Branch()
            if len(merchant_data) == 0:
                branch1.is_active=True
                branch1.address = "Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640"
                branch1.merchant = merchant
                branch1.area = "New Germany"
                branch1.save()
                
                branch2 = Branch()
                branch2.is_active=True
                branch2.address = "Shop 116A, Musgrave Centre, 115 Musgrave Rd, Berea, Durban, 4001"
                branch2.merchant = merchant
                branch2.area = "Durban Central"
                branch2.save()
            else:
                branch1.is_active=True
                branch1.address = merchant_data["address"]
                branch1.merchant = merchant
                branch1.area = merchant_data["branchAreas"][0]
                branch1.save()
        except Exception as e:
            pass
        return merchant
    
    def make_normal_account_super_admin(self, userAccountPk:int):
        userAccount = UserAccount.objects.get(pk=userAccountPk)
        userAccount.user.is_superuser = True
        userAccount.user.save()
        userAccount.can_create_merchants = True
        userAccount.save()
        return userAccount

    def create_product(self, merchant:MerchantBusiness, merchantUserAccount, name, price, discountPercent=0):
        try:
            branches = Branch.objects.filter(merchant=merchant)

            try:
                product = Product.objects.get(
                    name=name,
                )
            except:
                product = Product()
                product.name = name
                product.recommendedRetailPrice = 200
                product.image = "image"
                product.category = 1
                product.description = ""
                product.save()

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
    
    def make_date(self, daysFromNow):
        date = datetime.now() + timedelta(days=daysFromNow)
        date = date.strftime("%d %B %Y")
        return date