from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.products.models import BranchProduct, Product 
from django.urls import reverse

from global_test_config.global_test_config import GlobalTestCaseConfig


class ProductSearchViewTests(GlobalTestCaseConfig, TestCase):

    def setUp(self):
        merchant_user_account_1 = self.createMerchantUserAccount()
        merchant_user_account_2 = self.createMerchantUserAccount(
            {
                "username": "Max",
                "password": "HelloWorld",
                "firstName": "Max",
                "lastName": "Myers",
                "email": "maxmyers@gmail.com",
                "address": "72 rethman street newgermany",
                "phoneNumber": "0631837744",
                "isMerchant": True,
                "deviceToken": "fhwefhf2h3f9we7yfwefy32",
            }
        )

        merchant_business_1 = self.createMerchantBusiness(merchant_user_account_1)
        merchant_business_2 = self.createMerchantBusiness(merchant_user_account_2, merchantData={
            "name": "business_number_2",
            "email": "business2@gmail.com",
            "paygateId": "1234568",
            "paygateSecret": "secret",
            "address": "72 rethman street newgermany",
            "branchAreas": ["Durban", "Down the road"],
        })
        merchant_business_2.save()

        self.client = APIClient()

        self.product_1 = Product.objects.create(name="Dog Food")
        self.product_2 = Product.objects.create(name="My Cat Eats")

        self.branch_product1 = BranchProduct.objects.create(
            branch = merchant_business_1.branch_set.all()[0],
            createdBy = merchant_business_1.userAccount,
            product=self.product_1,
            branchPrice=50.00,
            inStock=True,
            isActive=True,
        )

        self.branch_product2 = BranchProduct.objects.create(
            branch=merchant_business_2.branch_set.all()[0],
            product=self.product_1,
            createdBy=merchant_user_account_2,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        # Branch product that should not appear in results
        self.branch_product3 = BranchProduct.objects.create(
            branch=merchant_business_1.branch_set.all()[0],
            product=self.product_2,
            createdBy=merchant_user_account_1,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        self.branch_product4 = BranchProduct.objects.create(
            branch=merchant_business_2.branch_set.all()[0],
            product=self.product_2,
            createdBy=merchant_user_account_2,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        return super().setUp()

    def test_search_with_results(self):

        # the GlobalTestCaseConfig class contains functions used by all test cases which I
        # created to make life a little easier:
        # GlobalTestCaseConfig also overrides the setup function so whatever extra data you need created
        # should be created there.

        url = reverse('search_products')
        response = self.client.get(url, {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][1]['branchPrice'], 75.00)

    def test_search_with_no_results(self):
        response = self.client.get(reverse('search_products'), {'query': 'Cat Food'})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], 'Failed to retrieve products')
        self.assertEqual(response.data['error'], 'No product matching this criteria was found')

    def test_search_with_empty_query(self):
        response = self.client.get(reverse('search_products'), {'query': ''})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'A search query was not specified')

    def test_search_excludes_inactive_or_out_of_stock(self):
        
        self.branch_product1.inStock = False
        self.branch_product1.save()

        response = self.client.get(reverse('search_products'), {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)

