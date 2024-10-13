from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.products.models import BranchProduct, Product 
from django.urls import reverse

class ProductSearchViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a product and related BranchProduct entries
        self.product = Product.objects.create(name="Dog Food")
        
        self.branch_product1 = BranchProduct.objects.create(
            product=self.product,
            branchPrice=50.00,
            inStock=True,
            isActive=True
        )
        
        self.branch_product2 = BranchProduct.objects.create(
            product=self.product,
            branchPrice=75.00,
            inStock=True,
            isActive=True
        )

        # Branch product that should not appear in results
        self.inactive_branch_product = BranchProduct.objects.create(
            product=self.product,
            branchPrice=100.00,
            inStock=False,  # Not in stock
            isActive=True
        )

        self.inactive_branch_product2 = BranchProduct.objects.create(
            product=self.product,
            branchPrice=100.00,
            inStock=True,
            isActive=False  # Not active
        )
    
    def test_search_with_results(self):
        """Test searching with a query that returns results."""
        response = self.client.get(reverse('product-search'), {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)  # Only 2 active and in-stock products
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][1]['branchPrice'], 75.00)

    def test_search_with_no_results(self):
        """Test searching with a query that returns no results."""
        response = self.client.get(reverse('product-search'), {'query': 'Cat Food'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 0)

    def test_search_with_empty_query(self):
        """Test searching with an empty query."""
        response = self.client.get(reverse('product-search'), {'query': ''})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 0)

    def test_search_excludes_inactive_or_out_of_stock(self):
        """Test that products not in stock or not active are excluded."""
        response = self.client.get(reverse('product-search'), {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_ids = [product['id'] for product in response.data['products']]

        # Ensure inactive and out-of-stock products are excluded
        self.assertNotIn(self.inactive_branch_product.id, product_ids)
        self.assertNotIn(self.inactive_branch_product2.id, product_ids)

