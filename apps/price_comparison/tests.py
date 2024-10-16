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
            inStock=False,  
            isActive=True
        )

        self.inactive_branch_product2 = BranchProduct.objects.create(
            product=self.product,
            branchPrice=100.00,
            inStock=True,
            isActive=False 
        )
    
    def test_search_with_results(self):
        response = self.client.get(reverse('product-search'), {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 2)
        self.assertEqual(response.data['products'][0]['branchPrice'], 50.00)
        self.assertEqual(response.data['products'][1]['branchPrice'], 75.00)

    def test_search_with_no_results(self):
        response = self.client.get(reverse('product-search'), {'query': 'Cat Food'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 0)

    def test_search_with_empty_query(self):
        response = self.client.get(reverse('product-search'), {'query': ''})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 0)

    def test_search_excludes_inactive_or_out_of_stock(self):
        response = self.client.get(reverse('product-search'), {'query': 'Dog Food'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_ids = [product['id'] for product in response.data['products']]

        self.assertNotIn(self.inactive_branch_product.id, product_ids)
        self.assertNotIn(self.inactive_branch_product2.id, product_ids)

