from django.test import TestCase
from rest_framework.reverse import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig
from apps.products.models import Product


class ProductTests(GlobalTestCaseConfig, TestCase):

    def test_create_product_as_merchant(self):
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchantBusiness(testMerchantAccount)
        _ = self.loginAsMerchant()
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
        _ = self.createNormalTestAccountAndLogin()
        self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchantBusiness(testMerchantAccount)
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
        _ = self.createNormalTestAccountAndLogin()
        self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchantBusiness(testMerchantAccount)
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
        _ = self.createNormalTestAccountAndLogin()
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchantBusiness(testMerchantAccount)
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
        _ = self.createNormalTestAccountAndLogin()
        self.makeNormalAccountSuperAdmin(self.userAccount.pk)
        testMerchantUserAccount = self.createTestMerchantUserAccount()
        merchant = self.createTestMerchantBusiness(testMerchantUserAccount)
        product1 = self.createTestProduct(
            merchant, testMerchantUserAccount, 
            name="Bob's Cat Food", price=200.0
        )
        product2 = self.createTestProduct(
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
        product = Product.objects.all().first()
        self.assertEqual(product.pk, product2.pk)

