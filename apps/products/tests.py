from django.test import TestCase
from rest_framework.reverse import reverse
from global_test_config.global_test_config import GlobalTestCaseConfig
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from apps.products.admin import ProductAdmin, BranchProductAdmin
from apps.accounts.models import UserAccount
from apps.products.models import GlobalProduct, BranchProduct
from apps.merchants.models import Branch, MerchantBusiness

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
        product = GlobalProduct.objects.filter(name=createProductPayload["name"]).first()
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
        product = GlobalProduct.objects.filter(name=createProductPayload["name"]).first()
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
        product = GlobalProduct.objects.filter(name=createProductPayload["name"]).first()
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
        product = GlobalProduct.objects.filter(name=createProductPayload["name"]).first()
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
        self.META = {}
        self.method = 'GET'
        self.GET = {}
        self.POST = {}

class AdminTests(TestCase):
    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.product_admin = ProductAdmin(GlobalProduct, self.site)
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
            is_active=True,
            device_token="test_token"  
        )
        return user_account

    def create_merchant_with_branch(self, merchant_name="Test Merchant"):
        """Helper method to create a merchant with branch"""
        user = User.objects.create_user(
            username=f"{merchant_name.lower().replace(' ', '')}_user",
            email=f"{merchant_name.lower().replace(' ', '')}@test.com",
            password='testpass123'
        )
        
        user_account = UserAccount.objects.create(
            user=user,
            phone_number=int(f"98765{abs(hash(merchant_name)) % 10000:04d}"),  
            is_merchant=True,  
            is_active=True,
            device_token=f"device_token_{merchant_name}"  
        )
        
        merchant = MerchantBusiness.objects.create(
            logo="test_logo.png",
            user_account=user_account,
            name=merchant_name,
            email=f"{merchant_name.lower().replace(' ', '')}@test.com",
            address="Test Address",
            paygate_reference="test_reference",
            paygate_id=f"PG_{merchant_name.lower().replace(' ', '')}",
            paygate_secret="test_secret",
            fernet_token="test_token"
        )
        
        branch = Branch.objects.create(
            merchant=merchant,
            is_active=True,
            address=f"{merchant_name} Address",
            area=MerchantBusiness.kloof
        )
        
        user_account.permitted_branches.add(branch)
        
        return user_account, merchant, branch

    def create_global_product(self, name="Test Product", price=100):
        """Helper method to create a global product"""
        return GlobalProduct.objects.create(
            name=name,
            description=f"Description for {name}",
            recommended_retail_price=price,
            photo=SimpleUploadedFile(
                name='test_photo.jpg',
                content=b'',
                content_type='image/jpeg'
            ),
            category=1
        )

    def create_branch_product(self, branch, global_product, created_by, price=100):
        """Helper method to create a branch product"""
        return BranchProduct.objects.create(
            branch=branch,
            product=global_product,
            branch_price=price,
            store_reference=f"REF-{branch.address}-{global_product.name}",
            created_by=created_by,
            merchant_name=branch.merchant.name,
            in_stock=True,
            is_active=True
        )

    def test_product_admin_superuser_queryset(self):
        """Test that superusers can see all products"""
        superuser_account = self.create_superuser()
        
        merchant1_account, merchant1, branch1 = self.create_merchant_with_branch("Merchant1")
        merchant2_account, merchant2, branch2 = self.create_merchant_with_branch("Merchant2")
        
        product1 = self.create_global_product("Product 1", 100)
        product2 = self.create_global_product("Product 2", 200)
        
        branch_product1 = self.create_branch_product(branch1, product1, merchant1_account)
        branch_product2 = self.create_branch_product(branch2, product2, merchant2_account)
        
        request = MockRequest(superuser_account.user)
        qs = self.product_admin.get_queryset(request)
        
        self.assertEqual(qs.count(), 2)
        self.assertIn(product1, qs)
        self.assertIn(product2, qs)

    def test_product_admin_merchant_queryset(self):
        """Test that merchants can only see their own products"""
        # Create first merchant
        merchant1_account, merchant1, branch1 = self.create_merchant_with_branch("Merchant1")
        merchant2_account, merchant2, branch2 = self.create_merchant_with_branch("Merchant2")
        
        product1 = self.create_global_product("Product 1", 100)
        product2 = self.create_global_product("Product 2", 200)
        
        branch_product1 = self.create_branch_product(
            branch=branch1,
            global_product=product1,
            created_by=merchant1_account,
            price=100
        )
        branch_product2 = self.create_branch_product(
            branch=branch2,
            global_product=product2,
            created_by=merchant2_account,
            price=200
        )
        
        request = MockRequest(merchant1_account.user)
        qs = self.product_admin.get_queryset(request)
        
        self.assertEqual(qs.count(), 1)
        self.assertIn(product1, qs)

    def test_branch_product_admin_save_model_new_instance(self):
        """Test that created_by is set correctly for new branch products"""
        merchant_account, merchant, branch = self.create_merchant_with_branch()
        global_product = self.create_global_product()
        
        new_branch_product = BranchProduct(
            branch=branch,
            product=global_product,
            branch_price=100,
            store_reference="TEST-REF",
            merchant_name=merchant.name,
            in_stock=True,
            is_active=True
        )
        
        request = MockRequest(merchant_account.user)
        self.branch_product_admin.save_model(request, new_branch_product, None, False)
        
        self.assertEqual(new_branch_product.created_by, merchant_account)

    def test_display_photo(self):
        """Test the display_photo method in ProductAdmin"""
        product = self.create_global_product()
        photo_html = self.product_admin.display_photo(product)
        self.assertIn('width="50"', photo_html)
        self.assertIn('height="50"', photo_html)
        self.assertIn('object-fit: cover', photo_html)

    def test_formfield_for_foreignkey_merchant(self):
        """Test that merchants can only select their own branches"""
        merchant_account, merchant, branch = self.create_merchant_with_branch()
        request = MockRequest(merchant_account.user)
        
        other_merchant_account, other_merchant, other_branch = self.create_merchant_with_branch("Other Merchant")
        
        formfield = self.branch_product_admin.formfield_for_foreignkey(
            BranchProduct._meta.get_field('branch'),
            request
        )
        
        self.assertEqual(formfield.queryset.count(), 1)
        self.assertIn(branch, formfield.queryset)
        self.assertNotIn(other_branch, formfield.queryset)

    def test_product_queryset_filtering(self):
        """Test that product queryset is properly filtered for merchants"""
        merchant_account, merchant, branch = self.create_merchant_with_branch()
        request = MockRequest(merchant_account.user)
        
        product1 = self.create_global_product("Product 1")
        product2 = self.create_global_product("Product 2")
        
        branch_product = self.create_branch_product(branch, product1, merchant_account) 
        
        qs = self.product_admin.get_queryset(request)
        
        self.assertEqual(qs.count(), 1)
        self.assertIn(product1, qs)
        self.assertNotIn(product2, qs)