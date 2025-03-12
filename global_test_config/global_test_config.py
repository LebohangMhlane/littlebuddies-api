from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import UserAccount
from apps.merchants.models import Branch, MerchantBusiness, SaleCampaign
from apps.products.models import BranchProduct, GlobalProduct
from rest_framework.authtoken.models import Token

# test functions shared by all tests


class MockedPaystackResponse:
    status_code = 200
    text = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&CHECKSUM=b41a77f83a275a849f23e30b4666e837"


class GlobalTestCaseConfig(TestCase):

    # TODO: remember to clean up test cases and move all repetitive tasks here:

    def setUp(self) -> None:

        # setup log in data:
        self.login_payload = {
            "email": "asandamhlane@gmail.com",
            "password": "ThisIsMyPassword",
        }

        # create default data:
        self.create_default_data()

    def create_default_data(self):

        # create a customer user account:
        self.customer_user_account, self.user_token = self.create_customer_user_account()

        # create a merchant user account:
        self.merchant_user_account = self.create_merchant_user_account()

        # create a branch:
        self.branch = self.create_a_branch(
            merchant_user_account=self.merchant_user_account
        )

        # create branch products:
        self.branch_product_1 = self.create_a_branch_product(
            branch=self.branch,
            merchant_user_account=self.merchant_user_account,
            item_number=1,
        )
        self.branch_product_2 = self.create_a_branch_product(
            branch=self.branch,
            merchant_user_account=self.merchant_user_account,
            item_number=2,
        )
        self.branch_product_3 = self.create_a_branch_product(
            branch=self.branch,
            merchant_user_account=self.merchant_user_account,
            item_number=3,
        )

        # create a sale campaign:
        self.create_a_sale_campaign(self.branch_product_2)

    def create_a_branch(
        self,
        custom_merchant_business={},
        custom_branch_data={},
        merchant_user_account=None,
    ):
        """
        ### if you want to create a merchant business with your own data then pass the required fields into the custom_merchant_business dictionary:
        """

        try:
            if len(custom_merchant_business) == 0:

                # first we create a merchant business:
                merchant = MerchantBusiness()
                merchant.logo = "My Company Logo"
                merchant.user_account = merchant_user_account
                merchant.name = "Orsum Pets"
                merchant.email = "orsumpets@gmail.com"
                merchant.address = (
                    "Shop 116A, Musgrave Centre, 115 Musgrave Rd, Berea, Durban, 4001"
                )
                merchant.delivery_fee = 20.00
                merchant.save()

                # create a dummy branch:
                branch = Branch()
                branch.is_active = True
                branch.address = (
                    "Shop 116A, Musgrave Centre, 115 Musgrave Rd, Berea, Durban, 4001"
                )
                branch.merchant = merchant
                branch.save()

                return branch
            else:
                # first we create a merchant business:
                merchant = MerchantBusiness()
                merchant.logo = custom_merchant_business["logo"]
                merchant.user_account = custom_merchant_business["user_account"]
                merchant.name = custom_merchant_business["name"]
                merchant.email = custom_merchant_business["email"]
                merchant.address = custom_merchant_business["address"]
                merchant.delivery_fee = custom_merchant_business["delivery_fee"]
                merchant.save()

                # create a dummy branch:
                branch = Branch()
                branch.is_active = custom_branch_data["is_active"]
                branch.address = custom_branch_data["address"]
                branch.merchant = merchant
                branch.save()

                return branch
        except Exception as e:
            print(f"Error creating branch: {e}")
            return None

    def create_customer_user_account(self, custom_user_data={}, custom_account_data={}):
        """
        ### if you want to create a user account with your own data then pass the required fields into the custom_account_data dictionary
        """

        # both instances must have custom data if either one has custom data:
        if len(custom_user_data) == 0 and len(custom_account_data) == 0:
            pass
        else:
            raise Exception(
                "If custom data is provided for one instance, you must provide custom data for both instances"
            )

        try:
            if len(custom_user_data) == 0:
                # first we create a dummy user:
                user = User()
                user.username = "johndoe0621837747"
                user.first_name = "John"
                user.last_name = "Doe"
                user.password = "ThisIsMyPassword"
                user.email = "asandamhlane@gmail.com"
                user.save()

                # now we can create a user account:
                user_account = UserAccount()
                user_account.user = user
                user_account.address = "71 rethman street newgermany"
                user_account.phone_number = "0621837747"
                user_account.is_merchant = False
                user_account.email_verified = True
                user_account.is_super_user = False
                user_account.device_token = "fhewofhew89f394ry34f7g4f"
                user_account.save()

                # create a token for the user:
                user_token = Token()
                user_token.user = user
                user_token.generate_key()
                user_token.save()

                # return the user account:
                return user_account, user_token.key
            else:
                # first we create a dummy user:
                user = User()
                user.first_name = custom_user_data["first_name"]
                user.last_name = custom_user_data["last_name"]
                user.password = custom_user_data["password"]
                user.email = custom_user_data["email"]
                user.save()

                # now we can create a user account:
                user_account = UserAccount()
                user_account.user = user
                user_account.address = custom_account_data["address"]
                user_account.phone_number = custom_account_data["phone_number"]
                user_account.is_merchant = custom_account_data["is_merchant"]
                user_account.email_verified = custom_account_data["email_verified"]
                user_account.is_super_user = custom_account_data["is_super_user"]
                user_account.device_token = custom_account_data["device_token"]
                user_account.save()

                # return the user account:
                return user_account
        except Exception as e:
            print(f"Error creating user account: {e}")
            return None

    def create_merchant_user_account(self, custom_user_data={}, custom_account_data={}):
        """
        ### if you want to create a user account with your own data then pass the required fields into the custom_account_data dictionary
        """

        # both instances must have custom data if either one has custom data:
        if len(custom_user_data) == 0 and len(custom_account_data) == 0:
            pass
        else:
            raise Exception(
                "If custom data is provided for one instance, you must provide custom data for both instances"
            )

        try:
            if len(custom_user_data) == 0:
                # first we create a dummy user:
                user = User()
                user.username = "janedoe0624834547"
                user.first_name = "Jane"
                user.last_name = "Doe"
                user.password = "ThisIsMyPassword"
                user.email = "jane@gmail.com"
                user.save()

                # now we can create a user account:
                user_account = UserAccount()
                user_account.user = user
                user_account.address = "53 rethman street newgermany"
                user_account.phone_number = "0624834547"
                user_account.is_merchant = True
                user_account.email_verified = True
                user_account.is_super_user = False
                user_account.device_token = "fhewofhew34235556f7g4f"
                user_account.save()

                # return the user account:
                return user_account
            else:
                # first we create a dummy user:
                user = User()
                user.first_name = custom_user_data["first_name"]
                user.last_name = custom_user_data["last_name"]
                user.password = custom_user_data["password"]
                user.email = custom_user_data["email"]
                user.save()

                # now we can create a user account:
                user_account = UserAccount()
                user_account.user = user
                user_account.address = custom_account_data["address"]
                user_account.phone_number = custom_account_data["phone_number"]
                user_account.is_merchant = custom_account_data["is_merchant"]
                user_account.email_verified = custom_account_data["email_verified"]
                user_account.is_super_user = custom_account_data["is_super_user"]
                user_account.device_token = custom_account_data["device_token"]
                user_account.save()

                # return the user account:
                return user_account
        except Exception as e:
            print(f"Error creating user account: {e}")
            return None

    def create_a_branch_product(
        self,
        branch=None,
        merchant_user_account=None,
        custom_global_product_data={},
        item_number=1,
    ):
        """
        #### if you want to create a global product with your own data then pass the required fields into the custom_global_product_data dictionary
        """

        try:
            if len(custom_global_product_data) == 0:
                # first we create a new global product:
                global_product = GlobalProduct()
                global_product.name = f"Dog Food-{item_number}"
                global_product.description = "A bag of dog food"
                global_product.recommended_retail_price = 100.00
                global_product.save()

                # if theres a branch, we create and return a branch product instead:
                if branch:
                    branch_product = BranchProduct()
                    branch_product.branch = branch
                    branch_product.global_product = global_product
                    branch_product.branch_price = 50.00
                    branch_product.created_by = merchant_user_account
                    branch_product.save()
                    return branch_product

                # else we return the global product:
                return global_product
            else:
                # first we create a new global product using provided custom product data:
                global_product = GlobalProduct()
                global_product.name = custom_global_product_data["name"]
                global_product.description = custom_global_product_data["description"]
                global_product.recommended_retail_price = custom_global_product_data[
                    "recommended_retail_price"
                ]
                global_product.save()

                # if theres a branch, we create and return a branch product instead:
                if branch:
                    branch_product = BranchProduct()
                    branch_product.branch = branch
                    branch_product.global_product = global_product
                    branch_product.branch_price = custom_global_product_data[
                        "branch_price"
                    ]
                    branch_product.created_by = custom_global_product_data["created_by"]
                    branch_product.save()

                # else we return the global product:
                return global_product
        except Exception as e:
            print(f"Error creating product: {e}")

    def create_a_sale_campaign(self, branch_product):
        sale_campaign = SaleCampaign()
        sale_campaign.branch = branch_product.branch
        sale_campaign.branch_product = branch_product
        sale_campaign.percentage_off = 50
        sale_campaign.save()

    def make_date(self, days_from_now):
        date = datetime.now() + timedelta(days=days_from_now)
        date = date.strftime("%d %B %Y")
        return date
