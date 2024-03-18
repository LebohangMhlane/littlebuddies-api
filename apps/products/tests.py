from django.test import TestCase
from rest_framework.reverse import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig
from apps.merchants.models import Product

class ProductTests(GlobalTestCaseConfig, TestCase):

    def test_create_product(self):
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 100,
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4 ",
            "discountPercentage": 0,
        }
        _ = self.createTestAccountAndLogin()
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchant(testMerchantAccount)
        self.makeUserAccountFullAdmin(self.userAccount.pk)
        createProductUrl = reverse("create_product_view")
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEquals(response.status_code, 200)
        self.assertEqual(createProductPayload["name"], response.data["product"]["name"])
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product != None)
        self.assertEqual(response.data["product"]["id"], product.pk)

    def test_create_product_failure(self):
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 0, # price can never be zero
            "inStock": False,
            "image": "secret",
            "storeReference": "ADDEHFIE12I4 ",
            "discountPercentage": 0,
        }
        _ = self.createTestAccountAndLogin()
        testMerchantAccount = self.createTestMerchantUserAccount()
        self.createTestMerchant(testMerchantAccount)
        self.makeUserAccountFullAdmin(self.userAccount.pk)
        createProductUrl = reverse("create_product_view")
        response = self.client.post(
            createProductUrl,
            data=createProductPayload,
            HTTP_AUTHORIZATION=f"Token {self.authToken}"
        )
        self.assertEquals(response.status_code, 500)
        product = Product.objects.filter(name=createProductPayload["name"]).first()
        self.assertTrue(product == None)