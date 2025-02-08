from django.db import connection
from django.test import TestCase
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta
from django.apps import apps

from apps.products.models import BranchProduct, GlobalProduct
from apps.merchants.models import SaleCampaign

from django.urls import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig


@pytest.fixture(autouse=True)
def clean_database(db):
    """
    Automatically clean up the database before each test.
    """
    for model in apps.get_models():
        model.objects.all().delete()
    reset_auto_increment_ids()

def reset_auto_increment_ids():
    """
    Reset the auto-increment counter for all tables to 1.
    """
    with connection.cursor() as cursor:
        # Disable foreign key checks to avoid constraints errors during truncation
        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

        # For MySQL and PostgreSQL, reset sequences (auto-increment primary key counters)
        for model in apps.get_models():
            table_name = model._meta.db_table
            # Reset the auto-increment for MySQL and PostgreSQL
            cursor.execute(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1;")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")


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
                "deliveryFee": "20.00"
            }
        )
        self.merchant_business_2.save()

        self.client = APIClient()

        # Create products
        self.product_1 = GlobalProduct.objects.create(name="Dog Food")
        self.product_2 = GlobalProduct.objects.create(name="My Cat Eats")

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

        campaign = SaleCampaign.objects.create(
            branch=self.branch_1,
            branch_product=self.branch_product1,  # Directly set the branch_product
            percentage_off=10,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        url = self.get_search_url('Dog Food', "1")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)
        self.assertIn('campaign', response.data['products'][0])
        self.assertAlmostEqual(response.data['products'][0]['campaign']['final_price'], 45.00)

    def test_products_ordered_by_final_price(self):
        campaign = SaleCampaign.objects.create(
                branch=self.branch_2,
                branch_product=self.branch_product2, 
                percentage_off=20,
                campaign_ends=datetime.now().date() + timedelta(days=5)
            )

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertLess(
            response.data['products'][0]['branch_price'],
            response.data['products'][1]['branch_price']
        )

    def test_products_ordered_by_final_price(self):
        campaign1 = SaleCampaign.objects.create(
            branch=self.branch_2,
            branch_product=self.branch_product2,  
            percentage_off=20,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        campaign2 = SaleCampaign.objects.create(
            branch=self.branch_1,
            branch_product=self.branch_product1,  
            percentage_off=5,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)

        first_product = response.data['products'][0]
        second_product = response.data['products'][1]

        first_expected_price = 47.50 
        second_expected_price = 60.00  

        self.assertEqual(float(first_product['campaign']['final_price']), first_expected_price)
        self.assertEqual(float(second_product['campaign']['final_price']), second_expected_price)

        self.assertLess(
            float(first_product['campaign']['final_price']),
            float(second_product['campaign']['final_price'])
        )

    def test_mixed_regular_and_campaign_price_ordering(self):

        campaign = SaleCampaign.objects.create(
            branch=self.branch_2,
            branch_product=self.branch_product2,  
            percentage_off=50,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)

        first_product = response.data['products'][0]
        second_product = response.data['products'][1]

        self.assertTrue('campaign' in first_product)
        self.assertEqual(float(first_product["campaign"]["final_price"]), 37.50)

        self.assertIsNone(second_product.get('campaign'))
        self.assertEqual(float(second_product['branch_price']), 50.00)

        self.assertLess(
            float(first_product['campaign']['final_price']),
            float(second_product['branch_price'])
        )

    def test_products_ordered_by_final_price(self):

        campaign1 = SaleCampaign.objects.create(
            branch=self.branch_2,
            branch_product=self.branch_product2, 
            percentage_off=20,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        campaign2 = SaleCampaign.objects.create(
            branch=self.branch_1,
            branch_product=self.branch_product1,  
            percentage_off=5,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)

        first_product = response.data['products'][0]
        second_product = response.data['products'][1]

        first_expected_price = 47.5
        second_expected_price = 60.00  

        self.assertEqual(float(first_product['campaign']['final_price']), first_expected_price)
        self.assertEqual(float(second_product['campaign']['final_price']), second_expected_price)

        self.assertLess(
            float(first_product['campaign']['final_price']),
            float(second_product['campaign']['final_price'])
        )

    def test_same_final_price_ordering(self):

        campaign = SaleCampaign.objects.create(
            branch=self.branch_2,
            branch_product=self.branch_product2,
            percentage_off=33.33,
            campaign_ends=datetime.now().date() + timedelta(days=5)
        )

        url = self.get_search_url('Dog Food', "1,2")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)

        first_product = response.data['products'][0]
        second_product = response.data['products'][1]

        first_price = (
            float(first_product['campaign']['final_price']) 
            if first_product.get('campaign') 
            else float(first_product['branch_price'])
        )

        second_price = (
            float(second_product['campaign']['final_price']) 
            if second_product.get('campaign') 
            else float(second_product['branch_price'])
        )

        self.assertTrue(
            (first_product.get('campaign') is None and second_product.get('campaign') is not None) or
            (first_product.get('campaign') is not None and second_product.get('campaign') is None)
        )

        regular_price = 50.00
        campaign_price = 51.00

        self.assertTrue(
            (abs(first_price - regular_price) < 0.01 and abs(second_price - campaign_price) < 0.01) or
            (abs(first_price - campaign_price) < 0.01 and abs(second_price - regular_price) < 0.01)
        )

        self.assertEqual(
            min(first_price, second_price),
            regular_price,
            "Regular priced product (50.00) should appear first"
        )
