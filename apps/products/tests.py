from django.test import TestCase
from rest_framework.reverse import reverse
from apps.merchants.models import Branch
from global_test_config.global_test_config import GlobalTestCaseConfig
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from apps.products.admin import ProductAdmin, BranchProductAdmin
from apps.products.models import Product, BranchProduct
from apps.products.models import BranchProduct, Product
from apps.accounts.models import UserAccount

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
            "in_stock": False,
            "image": "secret",
            "store_reference": "ADDEHFIE12I4 ",
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
        self.make_normal_account_super_admin(self.user_account.pk)
        testMerchantAccount = self.create_merchant_user_account()
        self.create_merchant_business(testMerchantAccount)
        createProductUrl = reverse("create_product_view")
        createProductPayload = {
            "merchantPk": 1,
            "name": "Ben's Cat Food",
            "description": "petfoodshop@gmail.com",
            "originalPrice": 100,
            "in_stock": False,
            "image": "secret",
            "store_reference": "ADDEHFIE12I4",
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
            "in_stock": False,
            "image": "secret",
            "store_reference": "ADDEHFIE12I4",
            "discountPercentage": 0,
        }
        _ = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.user_account.pk)
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
            "in_stock": False,
            "image": "secret",
            "store_reference": "ADDEHFIE12I4",
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
        self.make_normal_account_super_admin(self.user_account.pk)
        testmerchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(testmerchant_user_account)
        product1 = self.create_product(
            merchant, testmerchant_user_account, 
            name="Bob's Cat Food", price=200.0
        )
        product2 = self.create_product(
            merchant, testmerchant_user_account, 
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


class MockRequest:
    def __init__(self, user):
        self.user = user


class AdminTests(GlobalTestCaseConfig, TestCase):
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.product_admin = ProductAdmin(Product, self.site)
        self.branch_product_admin = BranchProductAdmin(BranchProduct, self.site)
        self.factory = RequestFactory()

    def create_superuser(self):
        """Helper method to create a superuser with associated UserAccount"""
        user = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        user.is_superuser = True
        user.is_staff = True
        user.save()
        
        user_account = UserAccount.objects.create(
            user=user,
            phone_number=1234567890,
            is_active=True
        )
        return user_account
    def create_merchant_with_branch(self, merchant_name="Test Merchant"):
        """Helper method to create a merchant with at least one branch"""
        merchant_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_account)
        merchant.save()  # Save the merchant before creating relationships
        
        # Create a branch for the merchant if none exists
        if not Branch.objects.filter(merchant=merchant).exists():
            Branch.objects.create(
                merchant=merchant,
                name=f"{merchant_name} Branch"
            )
        
        return merchant_account, merchant

    def test_product_admin_superuser_queryset(self):
        """Test that superusers can see all products"""
        # Create superuser with UserAccount
        superuser_account = self.create_superuser()
        
        # Create merchant and products with branch
        merchant_account, merchant = self.create_merchant_with_branch("Merchant1")
        branch_product1 = self.create_product(merchant, merchant_account, "Product 1", 100)
        branch_product2 = self.create_product(merchant, merchant_account, "Product 2", 200)
        
        # Get the actual Product instances
        product1 = branch_product1.product
        product2 = branch_product2.product
        
        # Test superuser can see all products
        request = MockRequest(superuser_account.user)
        qs = self.product_admin.get_queryset(request)
        self.assertEqual(qs.count(), 2)
        self.assertIn(product1, qs)
        self.assertIn(product2, qs)

    def test_product_admin_merchant_queryset(self):
        """Test that merchants can only see their own products"""
        # Create first merchant and products with branch
        merchant_account, merchant = self.create_merchant_with_branch("Merchant1")
        branch_product1 = self.create_product(merchant, merchant_account, "Product 1", 100)
        
        # Create another merchant and products with branch
        other_merchant_account, other_business = self.create_merchant_with_branch("Merchant2")
        branch_product2 = self.create_product(other_business, other_merchant_account, "Product 2", 200)
        
        # Get the actual Product instances
        product1 = branch_product1.product
        product2 = branch_product2.product
        
        # Verify merchant's user is properly set
        self.assertIsNotNone(merchant_account.user)
        
        # Test merchant can only see their products
        request = MockRequest(merchant_account.user)
        qs = self.product_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        self.assertIn(product1, qs)
        self.assertNotIn(product2, qs)

    def test_branch_product_admin_superuser_queryset(self):
        """Test that superusers can see all branch products"""
        superuser_account = self.create_superuser()
        merchant_account, merchant = self.create_merchant_with_branch()
        branch_product = self.create_product(merchant, merchant_account, "Test Product", 100)
        
        request = MockRequest(superuser_account.user)
        qs = self.branch_product_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        self.assertIn(branch_product, qs)

    def test_branch_product_admin_merchant_queryset(self):
        """Test that merchants can only see their own branch products"""
        # Create first merchant and branch products
        merchant_account, merchant = self.create_merchant_with_branch("Merchant1")
        branch_product1 = self.create_product(merchant, merchant_account, "Test Product", 100)
        
        # Create another merchant and branch products
        other_merchant_account, other_business = self.create_merchant_with_branch("Merchant2")
        branch_product2 = self.create_product(other_business, other_merchant_account, "Other Product", 200)
        
        request = MockRequest(merchant_account.user)
        qs = self.branch_product_admin.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        self.assertIn(branch_product1, qs)
        self.assertNotIn(branch_product2, qs)

    def test_branch_product_admin_foreign_key_restrictions(self):
        """Test that merchants can only select their own branches and products"""
        merchant_account, merchant = self.create_merchant_with_branch("Merchant1")
        branch_product1 = self.create_product(merchant, merchant_account, "Test Product", 100)
        
        other_merchant_account, other_business = self.create_merchant_with_branch("Merchant2")
        branch_product2 = self.create_product(other_business, other_merchant_account, "Other Product", 200)
        
        request = MockRequest(merchant_account.user)
        
        # Test branch field restrictions
        branch_field = self.branch_product_admin.formfield_for_foreignkey(
            BranchProduct._meta.get_field('branch'),
            request
        )
        self.assertIn(branch_product1.branch, branch_field.queryset)
        self.assertNotIn(branch_product2.branch, branch_field.queryset)
        
        # Test product field restrictions
        product_field = self.branch_product_admin.formfield_for_foreignkey(
            BranchProduct._meta.get_field('product'),
            request
        )
        self.assertIn(branch_product1.product, product_field.queryset)
        self.assertNotIn(branch_product2.product, product_field.queryset)

    def test_branch_product_admin_save_model(self):
        """Test that created_by is set correctly when saving new branch products"""
        merchant_account, merchant = self.create_merchant_with_branch()
        branch_product = self.create_product(merchant, merchant_account, "Test Product", 100)

        new_branch_product = BranchProduct(
            branch=branch_product.branch,
            product=branch_product.product,
            merchant_name="Test Merchant",
            branch_price=100,
            in_stock=True
        )

        request = MockRequest(merchant_account.user)
        self.branch_product_admin.save_model(request, new_branch_product, None, False)

        # Change the assertion to check for UserAccount instead of User
        self.assertEqual(new_branch_product.created_by, merchant_account)