from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch, MerchantBusiness, SaleCampaign
from apps.products.models import BranchProduct, GlobalProduct


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
            user__username=response.data["user_account"]["user"]["username"]
        )
        return testUserAccount

    def create_test_customer(self):
        userInputData = {
            "username": "customer",
            "password": "HelloWorld",
            "first_name": "Customer",
            "last_name": "IWantToOrder",
            "email": "customer@gmail.com",
            "address": "71 Rethman Street, New Germany, Durban",
            "phone_number": "0631837747",
            "is_merchant": False,
            "device_token": "cqmGKjazRUS5HfJypYk6r6:APA91bG0D4HYDz-21j2rK3mKP-M7HOAhcxR1_XEDCXUMqB4V_9Jd_1WFIAHq_zIw1o5LTPJUxJk4Xskzd4F1dO_OSk_bx4l48Jcac_KeXbGv5Fwj0aDZ-4-YsTEBvZei3t0dRgmw3yz0",
            "email_verified": True,
        }
        customer = User.objects.create(
            username=userInputData["username"],
            password=make_password(userInputData["password"]),
            first_name=userInputData["first_name"],
            last_name=userInputData["last_name"],
            email=userInputData["email"],
        )
        test_user_account = UserAccount.objects.create(
            user=customer,
            address=userInputData["address"],
            phone_number=userInputData["phone_number"],
            is_merchant=userInputData["is_merchant"],
            device_token=userInputData["device_token"],
            email_verified=userInputData["email_verified"],
        )
        token = Token.objects.create(user=customer)
        return test_user_account

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
        testmerchant_user_account = UserAccount.objects.get(user__email=userInputData["email"])
        return testmerchant_user_account

    def create_normal_test_account_and_login(self):
        user_account = self.create_normal_test_account()
        loginUrl = reverse("login")
        response = self.client.post(
            path=loginUrl,
            content_type=f"application/json",
            data=self.loginPayload,
        )
        self.authToken = response.data["token"]
        self.user_account = user_account
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
                merchant.delivery_fee = "20.00"
                merchant.closing_time = (datetime.now() + timedelta(hours=2)).time()
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
                merchant.delivery_fee = merchant_data["deliveryFee"]
                merchant.closing_time = (datetime.now() + timedelta(hours=2)).time()
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
                branch1.save()
        except Exception as e:
            pass
        return merchant

    def make_normal_account_super_admin(self, user_accountPk:int):
        user_account = UserAccount.objects.get(pk=user_accountPk)
        user_account.user.is_superuser = True
        user_account.user.save()
        user_account.can_create_merchants = True
        user_account.save()
        return user_account

    def create_product(self, merchant: MerchantBusiness, merchant_user_account, name, price, discountPercent=0):
        try:
            branches = Branch.objects.filter(merchant=merchant)
            if not branches.exists():
                raise ValueError(f"No branches found for the merchant: {merchant.name}")

            product, created = GlobalProduct.objects.get_or_create(
                name=name,
                defaults={
                    "recommended_retail_price": 200,
                    "image": "image",
                    "category": 1,
                    "description": "",
                },
            )

            branch_product = None  
            for branch in branches:
                branch_product = BranchProduct.objects.create(
                    branch=branch,
                    branch_price=product.recommended_retail_price + price,  
                    store_reference="3EERDE2",
                    created_by=merchant_user_account,
                    product=product,
                )

                if discountPercent > 0:
                    sale_campaign = SaleCampaign.objects.create(
                        branch=branch,
                        campaign_ends=datetime.now() + timedelta(days=5),
                        percentage_off=discountPercent,
                    )
                    sale_campaign.branch_product = branch_product
                    sale_campaign.save()

            return branch_product

        except Exception as e:
            print(f"Error creating product: {e}")
            raise

    def make_date(self, daysFromNow):
        date = datetime.now() + timedelta(days=daysFromNow)
        date = date.strftime("%d %B %Y")
        return date
