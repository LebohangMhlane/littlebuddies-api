from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta

from apps.products.models import BranchProduct, Product
from apps.merchants.models import SaleCampaign

from django.urls import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig

class ProductSearchViewTests(GlobalTestCaseConfig, TestCase):
    def setUp(self):
        # Create merchant user accounts
        self.merchant_user_1 = self.create_merchant_user_account()
        self.merchant_user_2 = self.create_merchant_user_account({
            "username": "Max",
            "password": "HelloWorld",
            "firstName": "Max",
            "lastName": "Myers",
            "email": "maxmyers@gmail.com",
            "address": "72 rethman street newgermany",
            "phoneNumber": "0631837744",
            "isMerchant": True,
            "deviceToken": "fhwefhf2h3f9we7yfwefy32",
        })

        # Create merchant businesses
        self.merchant_business_1 = self.create_merchant_business(self.merchant_user_1)
        self.merchant_business_2 = self.create_merchant_business(
            self.merchant_user_2,
            merchant_data={
                "name": "business_number_2",
                "email": "business2@gmail.com",
                "paygateId": "1234568",
                "paygateSecret": "secret",
                "address": "72 rethman street newgermany",
                "branchAreas": ["Durban", "Down the road"],
            }
        )
        self.merchant_business_2.save()

        self.client = APIClient()

        # Create products
        self.product_1 = Product.objects.create(name="Dog Food")
        self.product_2 = Product.objects.create(name="My Cat Eats")

        # Store branch IDs
        self.branch_1 = self.merchant_business_1.branch_set.first()
        self.branch_2 = self.merchant_business_2.branch_set.first()

        # Create branch products
        self.branch_product1 = BranchProduct.objects.create(
            branch=self.branch_1,
            created_by=self.merchant_business_1.user_account,
            product=self.product_1,
            branch_price=50.00,
            in_stock=True,
            is_active=True,
        )

        self.branch_product2 = BranchProduct.objects.create(
            branch=self.branch_2,
            product=self.product_1,
            created_by=self.merchant_user_2,
            branch_price=75.00,
            in_stock=True,
            is_active=True
        )

        self.branch_product3 = BranchProduct.objects.create(
            branch=self.branch_1,
            product=self.product_2,
            created_by=self.merchant_user_1,
            branch_price=75.00,
            in_stock=True,
            is_active=True
        )

        self.branch_product4 = BranchProduct.objects.create(
            branch=self.branch_2,
            product=self.product_2,
            created_by=self.merchant_user_2,
            branch_price=75.00,
            in_stock=True,
            is_active=True
        )

        return super().setUp()

    def get_search_url(self, query, store_ids=None):
        """Helper method to generate search URL"""
        kwargs = {'query': query}
        if store_ids is not None:
            kwargs['store_ids'] = str(store_ids)  # Convert to string as expected by the view
        return reverse('search_products', kwargs=kwargs)

    def test_search_with_results(self):
        """Test basic search functionality with results"""
        url = self.get_search_url('Dog Food', "1")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['branch_price'], "50.00")
        self.assertEqual(response.data['products'][0]['merchant_name'], 'Absolute Pets')

    def test_search_with_store_filter(self):
        """Test search with single store filter"""
        url = self.get_search_url('Dog Food', "1")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['branch_price'], "50.00")
        self.assertEqual(response.data['products'][0]['branch']['id'], self.branch_1.id)

    def test_search_with_multiple_store_filter(self):
        """Test search with multiple store filters"""
        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['branch_price'], "50.00")
        self.assertEqual(response.data['products'][1]['branch_price'], "75.00")

    def test_search_with_invalid_store_ids(self):
        """Test search with invalid store IDs format"""
        url = reverse('search_products', kwargs={'query': 'Dog Food', 'store_ids': 'invalid'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)

    def test_search_with_no_results(self):
        """Test search with no matching results"""
        url = self.get_search_url('NonexistentProduct', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], 'Failed to retrieve products.')
        self.assertEqual(response.data['error'], 'No product matching this criteria was found.')

    def test_search_with_empty_query(self):
        """Test search with empty query string"""
        url = self.get_search_url(" ", "1")  # Use a single space instead of empty string
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "A search query was not specified.")

    def test_search_excludes_inactive_or_out_of_stock(self):
        """Test that out of stock products are excluded"""
        self.branch_product1.in_stock = False
        self.branch_product1.save()

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)

    def test_search_with_nonexistent_store_ids(self):
        """Test search with store IDs that don't exist"""
        url = self.get_search_url('Dog Food', "4,5")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'No product matching this criteria was found.')

    def test_search_with_campaign(self):
        """Test search results with active campaign"""
        # Create campaign with required branch field
        campaign = SaleCampaign.objects.create(
            branch=self.branch_1,
            percentage_off=10,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )
        campaign.branch_products.add(self.branch_product1)
        
        url = self.get_search_url('Dog Food', "1")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertIn('campaign', response.data['products'][0])
        self.assertAlmostEqual(response.data['products'][0]['campaign']['final_price'], 45.00)

    def test_products_ordered_by_final_price(self):
        """Test that products are ordered by final price including campaigns"""
        # Create campaign with required branch field
        campaign = SaleCampaign.objects.create(
            branch=self.branch_2,
            percentage_off=20,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )
        campaign.branch_products.add(self.branch_product2)
        
        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertLess(
            response.data['products'][0]['branch_price'],
            response.data['products'][1]['branch_price']
        )