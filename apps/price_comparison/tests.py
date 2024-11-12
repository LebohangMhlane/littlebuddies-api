from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.products.models import BranchProduct, Product 
from django.urls import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig

class ProductSearchViewTests(GlobalTestCaseConfig, TestCase):

    def setUp(self):
        # Create merchant user accounts
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

        # Create merchant businesses
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

        # Create products
        self.product_1 = Product.objects.create(name="Dog Food")
        self.product_2 = Product.objects.create(name="My Cat Eats")

        # Store branch IDs for testing
        self.branch_1 = merchant_business_1.branch_set.first()
        self.branch_2 = merchant_business_2.branch_set.first()

        # Create branch products
        self.branch_product1 = BranchProduct.objects.create(
            branch=self.branch_1,
            createdBy=merchant_business_1.userAccount,
            product=self.product_1,
            branchPrice=50.00,
            inStock=True,
            isActive=True,
        )

        self.branch_product2 = BranchProduct.objects.create(
            branch=self.branch_2,
            product=self.product_1,
            createdBy=merchant_user_account_2,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        self.branch_product3 = BranchProduct.objects.create(
            branch=self.branch_1,
            product=self.product_2,
            createdBy=merchant_user_account_1,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        self.branch_product4 = BranchProduct.objects.create(
            branch=self.branch_2,
            product=self.product_2,
            createdBy=merchant_user_account_2,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        return super().setUp()

    def test_search_with_results(self):
        url = reverse('search_products', kwargs={'query': 'Dog Food', 'store_ids': [1]})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][0]['merchant_name'], 'Absolute Pets')

    def test_search_with_store_filter(self):
        url = reverse('search_products')
        response = self.client.get(url, {
            'query': 'Dog Food',
            'store_ids': f'{self.branch_1.id}'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][0]['branch']['id'], self.branch_1.id)

    def test_search_with_multiple_store_filter(self):
        url = reverse('search_products')
        response = self.client.get(url, {
            'query': 'Dog Food',
            'store_ids': f'{self.branch_1.id},{self.branch_2.id}'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][1]['branchPrice'], 75.00)

    def test_search_with_invalid_store_ids(self):
        url = reverse('search_products')
        response = self.client.get(url, {
            'query': 'Dog Food',
            'store_ids': 'invalid,ids'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'Invalid store IDs format')

    def test_search_with_no_results(self):
        url = reverse('search_products', kwargs={"query": "Cat Food"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], 'Failed to retrieve products')
        self.assertEqual(response.data['error'], 'No product matching this criteria was found')

    def test_search_with_empty_query(self):
        url = reverse('search_products', kwargs={"query": " "})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'A search query was not specified')

    def test_search_excludes_inactive_or_out_of_stock(self):
        self.branch_product1.inStock = False
        self.branch_product1.save()

        url = reverse('search_products', kwargs={"query": "Dog Food"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)

    def test_search_with_nonexistent_store_ids(self):
        url = reverse('search_products')
        response = self.client.get(url, {
            'query': 'Dog Food',
            'store_ids': '99999,88888' 
        })

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'No product matching this criteria was found')