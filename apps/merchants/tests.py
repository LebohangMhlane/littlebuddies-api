from unittest.mock import patch
from django.db import connection, transaction
from django.test import TestCase, RequestFactory, TransactionTestCase
from rest_framework.reverse import reverse
from django.contrib.admin.sites import AdminSite
from django.apps import apps

from apps.orders.models import Order
from apps.transactions.models import Transaction
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse
from apps.merchants.models import MerchantBusiness
from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
from apps.merchants.admin import MerchantBusinessAdmin, BranchAdmin, SaleCampaignAdmin


class MerchantTests(GlobalTestCaseConfig, TestCase):

    # little buddies tests:

    def test_get_store_range(self):

        merchant_user_account = self.create_merchant_user_account({})
        merchantBusiness = self.create_merchant_business(merchant_user_account)

        _ = self.create_product(merchantBusiness, merchant_user_account, "Bob's dog food", 100)
        _ = self.create_product(merchantBusiness, merchant_user_account, "Bob's dog food", 50, 10)

        customer = self.create_test_customer()
        authToken = self.login_as_customer()

        storeRangeUrl = reverse('get_store_range', args=['randomCoordinates']) # TODO: remember to test finding a store range within the devices radius
        response = self.client.get(
            storeRangeUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}"
        )

        self.assertEqual(len(response.data["petstores"]), 1)

    def test_get_nearest_branch(self):

        _ = self.create_test_customer()
        authToken = self.login_as_customer()

        merchant_user_account = self.create_merchant_user_account({
            "username": "Lebo",
            "password": "Hello World",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebo@gmail.com",
            "address": "24 Tiger Lily Street",
            "phoneNumber": "0638473382",
            "isMerchant": True,
            "deviceToken": "dfwhefoewhofh328rh2"
        })

        merchantBusiness = self.create_merchant_business(
            merchant_user_account, merchant_data={
                "name": "Orsum Pets",
                "email": "orsumpets@gmail.com",
                "address": 'Shop No, 55 Shepstone Rd, New Germany, Durban, 3610, South Africa',
                "paygateReference": "pgtest_123456789",
                "paygateId": "339e8g3iiI934",
                "paygateSecret": "secretSanta",
                "branchAreas": ["New Germany"],
                "hasSpecials": False,
            }
        )

        _ = self.create_product(merchantBusiness, merchant_user_account, "Bob's dog food", 100)
        _ = self.create_product(merchantBusiness, merchant_user_account, "Bob's dog food", 50, 10)

        # deviceLocation = "85 Dorothy Nyembe St, Durban Central, Durban, 4001"
        # deviceLocation = "-29.857298, 31.024362"
        deviceLocation = "-29.7799367,30.875305"
        getNearestBranchUrl = reverse(
            "get_nearest_branch",
            kwargs={"coordinates": deviceLocation, "merchantId": merchantBusiness.pk},
        )

        response = self.client.get(
            getNearestBranchUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}"
        )

        self.assertEqual(response.data["message"], "Nearest branch retrieved successfully")
        self.assertEqual(response.data["nearestBranch"]["distance"]["distance"]["text"], "3.1 km")
        self.assertEqual(response.data["nearestBranch"]["branch"]["id"], 9)
        self.assertEqual(response.data["nearestBranch"]["products"][0]["product"]["name"], "Bob's dog food")

    def test_get_updated_petstores_near_me(self):
        _ = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account1 = self.create_merchant_user_account({})
        merchantBusiness1 = self.create_merchant_business(merchant_user_account1, {})
        merchant_user_account2 = self.create_dynamic_merchant_user_account({
            "username": "Lebo",
            "password": "Hello World",
            "firstName": "Lebohang",
            "lastName": "Mhlane",
            "email": "lebo@gmail.com",
            "address": "24 Tiger Lily Street",
            "phoneNumber": "0638473382",
            "isMerchant": True,
            "deviceToken": "dfwhefoewhofh328rh2"
        })
        merchantBusiness2 = self.create_merchant_business(
            merchant_user_account2, {
                "name": "Totally Pets",
                "email": "totallypets@gmail.com",
                "address": "197 Brand Rd, Bulwer, Berea, 4083",
                "paygateReference": "pgtest_123456789",
                "paygateId": "339e8g3iiI934",
                "paygateSecret": "santafridays",
                "branchAreas": ["New Germany"],
                "hasSpecials": False,
            }
        )

        p1 = self.create_product(merchantBusiness1, merchant_user_account1, "Bob's dog food", 200)
        p2 = self.create_product(merchantBusiness1, merchant_user_account1, "Bob's cat food", 100)

        p3 = self.create_product(merchantBusiness2, merchant_user_account2, "Bob's cat food", 100)
        p4 = self.create_product(merchantBusiness2, merchant_user_account2, "Bob's cat food", 100)

        getNearByStoresUrl = reverse("get_updated_petstores_near_me", kwargs={
        "storeIds": '[{"id": 1, "distance": "10 mins"}, {"id": 2, "distance": "10 mins"}]'
        })
        response = self.client.get(
            getNearByStoresUrl,
            HTTP_AUTHORIZATION=f"Token {authToken}"
        )
        pass

    def test_create_merchant(self):
        create_merchant_payload = {
            "user_accountPk": 2,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.user_account.pk)
        merchant_user_account = self.create_merchant_user_account({})
        create_merchant_url = reverse("create_merchant_view")
        create_merchant_payload["user_accountPk"] = merchant_user_account.pk
        response = self.client.post(
            create_merchant_url,
            data=create_merchant_payload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 200)
        merchant = MerchantBusiness.objects.filter(name=create_merchant_payload["name"]).first()
        self.assertEqual(merchant.user_account.pk, merchant_user_account.pk)
        self.assertEqual(response.data["merchant"]["name"], create_merchant_payload["name"])

    def test_unauthorized_create_merchant(self):
        createMerchantPayload = {
            "user_accountPk": 1,
            "name": "Pet Food Shop",
            "email": "petfoodshop@gmail.com",
            "address": "12 Pet Street Newgermany",
            "paygateId": "10011072130",
            "paygateSecret": "secret",
        }
        token = self.create_normal_test_account_and_login()
        createMerchantUrl = reverse("create_merchant_view")
        response = self.client.post(
            createMerchantUrl,
            data=createMerchantPayload,
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 401)
        merchant = MerchantBusiness.objects.filter(name=createMerchantPayload["name"]).first()
        self.assertEqual(merchant, None)

    def test_deactivate_merchant(self):
        testAccountToken = self.create_normal_test_account_and_login()
        self.make_normal_account_super_admin(self.user_account.pk)
        testmerchant_user_account = self.create_merchant_user_account({})
        merchant = self.create_merchant_business(testmerchant_user_account)
        self.assertEqual(merchant.is_active, True)
        payload = {
            "merchantId": merchant.pk,
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        merchant = MerchantBusiness.objects.get(pk=payload["merchantId"])
        self.assertEqual(merchant.is_active, False)

    def test_deactivate_merchant_failure(self):
        testAccountToken = self.create_normal_test_account_and_login()
        _ = self.make_normal_account_super_admin(self.user_account.pk)
        testmerchant_user_account = self.create_merchant_user_account()
        merchant_business = self.create_merchant_business(testmerchant_user_account)
        self.assertEqual(merchant_business.is_active, True)
        payload = {
            "merchantId": 100, # id doesn't exist
        }
        deleteMerchantUrl = reverse("deactivate_merchant_view")
        response = self.client.post(
            deleteMerchantUrl,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["message"], "Failed to deactivate merchant")
        self.assertFalse(response.data["success"])
        merchant_business = MerchantBusiness.objects.get(pk=merchant_business.pk)
        self.assertEqual(merchant_business.is_active, True)

    def test_update_merchant(self):
        testAccountToken = self.create_normal_test_account_and_login()
        _ = self.make_normal_account_super_admin(self.user_account.pk)
        test_merchant_user_account = self.create_merchant_user_account()
        merchant_business = self.create_merchant_business(test_merchant_user_account)
        self.assertEqual(merchant_business.name, "Absolute Pets")
        self.assertEqual(merchant_business.address, "Absolute Pets Village @ Kloof, Shop 33, Kloof Village Mall, 33 Village Rd, Kloof, 3640")
        payload = {
            "merchantPk": merchant_business.pk,
            "name": "World of pets",
            "address": "32 rethman street newgermany",
        }
        update_merchant_url = reverse("update_merchant_view")
        response = self.client.post(
            update_merchant_url,
            data=payload,
            HTTP_AUTHORIZATION=f"Token {testAccountToken}"
        )
        updated_merchant = response.data["updatedMerchant"]
        self.assertEqual(updated_merchant["name"], "World of pets")
        self.assertEqual(updated_merchant["address"], "32 rethman street newgermany")

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_acknowlegde_order(self, mocked_response, mocked_send_notification):

        mocked_response.return_value = MockedPaygateResponse()

        _ = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
        checkout_form_payload = {
            "branchId": str(merchant.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantity_ordered': 1}, {'id': 2, 'quantity_ordered': 2}]",
            "delivery": True,
            "deliveryDate": self.make_date(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        payment_notification_response = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        _ = self.client.post(
            payment_notification_url,
            data=payment_notification_response,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()

        # merchant should now acknowledge the order:
        acknowledge_order_url = reverse("acknowledge_order_view", kwargs={"orderPk": order.pk}) 
        merchantAuthToken = self.login_as_merchant()
        response = self.client.get(
            acknowledge_order_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {merchantAuthToken}",
        )
        order = Order.objects.all().first()
        self.assertEqual(response.data["message"], "Order acknowledged successfully")
        self.assertTrue(order.acknowledged)

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_fulfill_order(self, mocked_response, mocked_send_notification):

        mocked_response.return_value = MockedPaygateResponse()

        _ = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
        branch = merchant.branch_set.all().first()
        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': %s, 'quantity_ordered': 1}, {'id': %s, 'quantity_ordered': 2}]" % (p1.pk, p2.pk),
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.make_date(daysFromNow=1),
            "address": "71 downthe street Bergville",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        payment_notification_response = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        _ = self.client.post(
            payment_notification_url,
            data=payment_notification_response,
            content_type='application/x-www-form-urlencoded'
        )

        # merchant should now acknowledge the order at this point:
        order = Order.objects.all().first()
        acknowledge_order_url = reverse("acknowledge_order_view", kwargs={"orderPk": order.pk}) 
        merchant_auth_token = self.login_as_merchant()
        acknowledge_order_response = self.client.get(
            acknowledge_order_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {merchant_auth_token}",
        )

        fulfill_order_url = reverse("fulfill_order_view", kwargs={"orderPk": order.pk})
        fulfill_order_response = self.client.get(
            fulfill_order_url,
            HTTP_AUTHORIZATION=f"Token {merchant_auth_token}",
        )
        order_from_response = fulfill_order_response.data["order"]
        self.assertEqual(order_from_response["status"], Order.DELIVERED)
        self.assertTrue(order_from_response["acknowledged"])
        self.assertEqual(order_from_response["transaction"]["status"], Transaction.COMPLETED)


class AdminFilterTests(GlobalTestCaseConfig, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        
        self.normal_user_token = self.create_normal_test_account_and_login()
        
        self.site = AdminSite()
        self.merchant_admin = MerchantBusinessAdmin(MerchantBusiness, self.site)
        self.branch_admin = BranchAdmin(Branch, self.site)
        self.campaign_admin = SaleCampaignAdmin(SaleCampaign, self.site)

        self.merchant_user_account1 = self.create_merchant_user_account({
            "username": "Merchant1",
            "password": "HelloWorld",  
            "firstName": "Test",
            "lastName": "Merchant1",
            "email": "mikemyers@gmail.com",  
            "address": "24 Test Street",
            "phoneNumber": "0631234567",
            "isMerchant": True,
            "deviceToken": "test_token_1"
        })
        
        self.merchant1 = self.create_merchant_business(
            self.merchant_user_account1,
            merchant_data={
                "name": "Test Store 1",
                "email": "store1@test.com",
                "address": "Shop No, 55 Test Rd, Test Area, Test City, 3610",
                "paygateReference": "pgtest_123456789",
                "paygateId": "TEST1",
                "paygateSecret": "secret1",
                "branchAreas": ["Test Area"],
                "hasSpecials": False,
            }
        )

        self.merchant_user_account2 = self.create_merchant_user_account({
            "username": "Merchant2",
            "password": "HelloWorld",  
            "firstName": "Test",
            "lastName": "Merchant2",
            "email": "merchant2@test.com",
            "address": "25 Test Street",
            "phoneNumber": "0637654321",
            "isMerchant": True,
            "deviceToken": "test_token_2"
        })
        
        self.merchant2 = self.create_merchant_business(
            self.merchant_user_account2,
            merchant_data={
                "name": "Test Store 2",
                "email": "store2@test.com",
                "address": "Shop No, 56 Test Rd, Test Area, Test City, 3610",
                "paygateReference": "pgtest_987654321",
                "paygateId": "TEST2",
                "paygateSecret": "secret2",
                "branchAreas": ["Test Area"],
                "hasSpecials": False,
            }
        )

        self.branch2 = Branch.objects.create(
            address="Branch 2",
            area="Test Area 2",
            merchant=self.merchant2
        )

        self.campaign1 = SaleCampaign.objects.create(
            branch=self.merchant1.branch_set.first(),
            percentage_off=10
        )
        self.campaign2 = SaleCampaign.objects.create(
            branch=self.branch2,
            percentage_off=20
        )

    def test_merchant_admin_superuser_access(self):
        """Test superuser can see all merchants in admin"""
        self.make_normal_account_super_admin(self.user_account.pk)  
        request = self.factory.get('/')
        request.user = self.user_account.user
        
        queryset = self.merchant_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.merchant1, queryset)
        self.assertIn(self.merchant2, queryset)

    def test_merchant_admin_merchant_access(self):
        """Test merchant can only see their own business in admin"""
        merchant_token = self.login_as_merchant()  
        request = self.factory.get('/')
        request.user = self.merchant_user_account1.user
        
        queryset = self.merchant_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.merchant1)

    def test_branch_admin_superuser_access(self):
        """Test superuser can see all branches in admin"""
        self.make_normal_account_super_admin(self.user_account.pk) 
        request = self.factory.get('/')
        request.user = self.user_account.user
        
        queryset = self.branch_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 3)  

    def test_branch_admin_merchant_access(self):
        """Test merchant can only see their own branches in admin"""
        merchant_token = self.login_as_merchant()  
        request = self.factory.get('/')
        request.user = self.merchant_user_account1.user
        
        queryset = self.branch_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().merchant, self.merchant1)

    def test_campaign_admin_superuser_access(self):
        """Test superuser can see all campaigns in admin"""
        self.make_normal_account_super_admin(self.user_account.pk)  
        request = self.factory.get('/')
        request.user = self.user_account.user
        
        queryset = self.campaign_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.campaign1, queryset)
        self.assertIn(self.campaign2, queryset)

    def test_campaign_admin_merchant_access(self):
        """Test merchant can only see their own campaigns in admin"""
        merchant_token = self.login_as_merchant()  
        request = self.factory.get('/')
        request.user = self.merchant_user_account1.user
        
        queryset = self.campaign_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.campaign1)

    def test_campaign_admin_foreign_key_filtering(self):
        """Test campaign foreign key fields are properly filtered for merchant"""
        merchant_token = self.login_as_merchant()  
        request = self.factory.get('/')
        request.user = self.merchant_user_account1.user
        
        branch_field = self.campaign_admin.formfield_for_foreignkey(
            SaleCampaign._meta.get_field('branch'),
            request
        )
        self.assertEqual(branch_field.queryset.count(), 1)
        self.assertEqual(
            branch_field.queryset.first().merchant,
            self.merchant1
        )

    def test_unauthorized_admin_access(self):
        """Test unauthorized user cannot access admin pages"""
        self.create_test_customer()
        token = self.login_as_customer()
        
        response = self.client.post(
            reverse('create_merchant_view'),
            data={
                "name": "Test Store",
                "email": "test@test.com",
                "address": "Test Address",
            },
            HTTP_AUTHORIZATION=f"Token {token}"
        )
        self.assertEqual(response.status_code, 401)
