from django.test import TestCase
from rest_framework.reverse import reverse
from apps.merchants.models import Branch
from global_test_config.global_test_config import GlobalTestCaseConfig
from apps.products.models import BranchProduct, Product


class ProductTests(GlobalTestCaseConfig, TestCase):

    def test_create_product_as_merchant(self):
        testMerchantAccount = self.create_merchant_user_account()
        self.create_merchant_business(testMerchantAccount)
        _ = self.login_as_merchant()
        createProductUrl = reverse("create_product_view")
        createProductPayload = {
            "merchantPk": testMerchantAccount.pk,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 100,
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4 ",
            "discountPercentage": 0,
        }
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(createProductPayload["name"], response.data["product"]["name"])
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product != None)
        self.assertEqual(response.data["product"]["id"], product.pk)

    def test_create_product_as_superadmin(self):
        _ = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.userAccount.pk)
        testMerchantAccount = self.create_merchant_user_account()
        self.create_merchant_business(testMerchantAccount)
        createProductUrl = reverse("create_product_view")
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 100,
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4",
            "discountPercentage": 0,
        }
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(createProductPayload["name"], response.data["product"]["name"])
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product != None)
        self.assertEqual(response.data["product"]["id"], product.pk)

    def test_invalid_product_creation(self):
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 0, # price can never be zero
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4",
            "discountPercentage": 0,
        }
        _ = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.userAccount.pk)
        testMerchantAccount = self.create_merchant_user_account()
        self.create_merchant_business(testMerchantAccount)
        createProductUrl = reverse("create_product_view")
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEqual(response.status_code, 500)
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product == None)

    def test_create_product_as_customer_failure(self):
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 230,
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4",
            "discountPercentage": 0,
        }
        _ = self.create_normal_test_account_and_login()
        testMerchantAccount = self.create_merchant_user_account()
        self.create_merchant_business(testMerchantAccount)
        createProductUrl = reverse("create_product_view")
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEqual(response.status_code, 500)
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product == None)

    def test_delete_product_as_superadmin(self):
        _ = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.userAccount.pk)
        testMerchantUserAccount = self.create_merchant_user_account()
        merchant = self.create_merchant_business(testMerchantUserAccount)
        product1 = self.create_product(
            merchant, testMerchantUserAccount, 
            name="Bob's Cat Food", price=200.0
        )
        product2 = self.create_product(
            merchant, testMerchantUserAccount, 
            name="Bob's Dog Food", price=200.0
        )
        deleteProductUrl = reverse(
            "delete_product_view", 
            kwargs={"productPk": product1.pk}
        )
        response = self.client.get(
            deleteProductUrl,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEqual(
            response.data["message"], 
            "Product deleted successfully"
        )
        branch = Branch.objects.get(id=2)
        product = BranchProduct.objects.filter(branch=branch).first()
        self.assertEqual(product.pk, product2.pk)

