from unittest.mock import patch
from django.test import TestCase
from rest_framework.reverse import reverse
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from django.core.mail import send_mail
from decimal import Decimal

from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderedProduct, record_cancellation
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse
from apps.transactions.models import Transaction
from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness, Branch, SaleCampaign
from apps.products.models import Product, BranchProduct

User = get_user_model()

class OrderTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_create_order(self, mocked_response, mocked_send_notification):

        mocked_response.return_value = MockedPaygateResponse()

        customer = self.create_test_customer()
        authToken = self.login_as_customer()
        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)
        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)
        branch = merchant.branch_set.all().first()
        checkout_form_payload = {
            "branchId": str(merchant.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantity_ordered': 1}, {'id': 2, 'quantity_ordered': 2}]",
            "discountTotal": "0",
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
        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        response = self.client.post(
            payment_notification_url,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()
        products = order.transaction.products_purchased.filter(id__in=[p1.id, p2.id])
        self.assertEqual(products[0].id, p1.id)
        self.assertEqual(order.transaction.branch.id, int(checkout_form_payload["branchId"]))
        self.assertEqual(order.status, Order.PENDING_DELIVERY)
        self.assertEqual(order.transaction.customer.id, customer.id)

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_get_all_orders_as_customer(self, mocked_response, mocked_send_notification):

        mocked_response.return_value = MockedPaygateResponse()

        customer = self.create_test_customer()
        customer_auth_token = self.login_as_customer()

        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)

        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantity_ordered': 1}, {'id': 2, 'quantity_ordered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.make_date(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiate_payment_response = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {customer_auth_token}",
        )

        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        paymentNotificatonResponse = self.client.post(
            payment_notification_url,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )

        getAllOrdersUrl = reverse("get_all_orders_view")
        getAllOrdersResponse = self.client.get(
            getAllOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {customer_auth_token}"
        )
        order = Order.objects.all().first()
        orderFromResponse = getAllOrdersResponse.data["orders"][0]
        self.assertEqual(
            orderFromResponse["id"], order.id
        )
        self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            orderFromResponse["transaction"]["branch"]["id"],
            int(checkout_form_payload["branchId"]),
        )
        self.assertEqual(
            float(orderFromResponse["transaction"]["amount"]), 
            float(checkout_form_payload["totalCheckoutAmount"])
        )

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.send_transaction_status_notification")
    @patch("apps.paygate.views.PaymentInitializationView.send_initiate_payment_request_to_paygate")
    def test_get_all_orders_as_merchant(self, mocked_response, mocked_send_notification):

        mocked_response.return_value = MockedPaygateResponse()

        customer = self.create_test_customer()
        customer_auth_token = self.login_as_customer()

        merchant_user_account = self.create_merchant_user_account()
        merchant = self.create_merchant_business(merchant_user_account)

        p1 = self.create_product(merchant, merchant_user_account, "Bob's dog food", 200)
        p2 = self.create_product(merchant, merchant_user_account, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkout_form_payload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantity_ordered': 1}, {'id': 2, 'quantity_ordered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.make_date(1),
            "address": "71 down the street Bergville",
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiate_payment_response = self.client.post(
            initiate_payment_url,
            data=checkout_form_payload,
            HTTP_AUTHORIZATION=f"Token {customer_auth_token}",
        )

        payment_notification_response = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        payment_notification_url = reverse("payment_notification_view")
        _ = self.client.post(
            payment_notification_url,
            data=payment_notification_response,
            content_type='application/x-www-form-urlencoded'
        )

        merchant_auth_token = self.login_as_merchant()

        get_all_orders_url = reverse("get_all_orders_view")
        get_all_orders_response = self.client.get(
            get_all_orders_url,
            HTTP_AUTHORIZATION=f"Token {merchant_auth_token}"
        )
        order = Order.objects.all().first()
        order_from_response = get_all_orders_response.data["orders"][0]
        self.assertEqual(
            order_from_response["id"], order.id
        )
        self.assertEqual(order_from_response["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            order_from_response["transaction"]["branch"]["id"],
            int(checkout_form_payload["branchId"]),
        )
        self.assertEqual(
            float(order_from_response["transaction"]["amount"]), 
            float(checkout_form_payload["totalCheckoutAmount"])
        )

class CancelOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer_user = User.objects.create_user(
            username="test_customer", 
            email="customer@example.com",
            password="testpassword123"
        )
        self.customer_account = UserAccount.objects.create(
            user=self.customer_user,
            phone_number=1234567890,
            device_token='test_device_token_1',
            is_merchant=True 
        )

        self.another_customer_user = User.objects.create_user(
            username="another_customer", 
            email="another_customer@example.com",
            password="testpassword123"
        )
        self.another_customer_account = UserAccount.objects.create(
            user=self.another_customer_user,
            phone_number=9876543210,
            device_token='test_device_token_2',
            is_merchant=True 
        )

        self.merchant_user = User.objects.create_user(
            username="merchant", 
            email="merchant@example.com",
            password="merchantpassword123"
        )
        self.merchant_account = UserAccount.objects.create(
            user=self.merchant_user,
            phone_number=5555555555,
            device_token='merchant_device_token',
            is_merchant=True 
        )

        self.merchant_business = MerchantBusiness.objects.create(
            user_account=self.merchant_account,
            name="Test Merchant Business",
            email="merchant@example.com"
        )

        self.branch = Branch.objects.create(
            merchant=self.merchant_business,
            address='123 Test St',
            area='Test Area',  
            is_active=True    
        )

        self.customer_transaction = Transaction.objects.create(
            customer=self.customer_account,
            branch=self.branch
        )

        self.pending_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.PENDING_DELIVERY,
            acknowledged=True
        )
        self.cancelled_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.CANCELLED,
            acknowledged=False
        )
        self.delivered_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.DELIVERED,
            acknowledged=True
        )

        self.pending_order = Order.objects.create(
                transaction=self.customer_transaction,
                status=Order.PENDING_DELIVERY,
                acknowledged=True
            )

        self.cancel_order_url = reverse(
            "cancel-order", kwargs={"order_id": self.pending_order.id}
        )

    def _authenticate_customer(self, user=None):
        user = user or self.customer_user
        self.client.force_authenticate(user=user)

    def test_cancel_order_success(self):
        self._authenticate_customer()  

        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Order cancelled successfully!")

    def test_cancel_order_unauthenticated(self):
        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_order_different_customer(self):
        self._authenticate_customer(user=self.another_customer_user)

        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_order_missing_order_id(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel-order", kwargs={"order_id": 0}
        )

        response = self.client.post(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(response.data.get('message'), "Order ID is required!")

    def test_cancel_order_invalid_order_id(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel-order", kwargs={"order_id": 99999}
        )
        response = self.client.post(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_already_cancelled_order(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel-order", kwargs={"order_id": self.cancelled_order.pk}
        )
        response = self.client.post(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(
            response.data.get('message'), 
            "Order cannot be cancelled at this stage."
        )

    def test_cancel_delivered_order(self):
        self._authenticate_customer()

        self.cancel_order_url = reverse(
            "cancel-order", kwargs={"order_id": self.delivered_order.pk}
        )
        response = self.client.post(self.cancel_order_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(
            response.data.get('message'), 
            "Order cannot be cancelled at this stage."
        )

    def test_record_cancellation_creation(self):
        """Test basic cancellation record creation"""
        cancelled_order = record_cancellation(
            order=self.pending_order,
            user_account=self.customer_account,
            reason='CUSTOMER_REQUEST',
            notes='Test cancellation',
            refund_amount=Decimal('100.00')
        )

        self.assertEqual(cancelled_order.order, self.pending_order)
        self.assertEqual(cancelled_order.cancelled_by, self.customer_account)
        self.assertEqual(cancelled_order.reason, 'CUSTOMER_REQUEST')
        self.assertEqual(cancelled_order.additional_notes, 'Test cancellation')
        self.assertEqual(cancelled_order.refund_amount, Decimal('100.00'))
        self.assertTrue(cancelled_order.refund_initiated)

class RepeatOrderViewTestCase(TestCase):
    def setUp(self):

        def create_a_sale_campaign(branch_product, branch):
            sale_campaign = SaleCampaign()
            sale_campaign.branch_product = branch_product
            sale_campaign.branch = branch
            sale_campaign.percentage_off = 50
            sale_campaign.save()

        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser', 
            email='testuser@example.com',
            password='testpassword'
        )

        self.user_account = UserAccount.objects.create(
            user=self.user, 
            phone_number=1234567890,
            is_merchant=True,
            device_token='test_device_token'
        )

        self.merchant = MerchantBusiness.objects.create(
            user_account=self.user_account,
            name='Test Merchant',
            logo='merchant_logo_url',
            email='merchant@example.com',
            address='123 Test St',
            paygate_reference='test_ref',
            paygate_id='test_id',
            paygate_secret='test_secret'
        )

        self.branch = Branch.objects.create(
            merchant=self.merchant,
            address='123 Test St',
            area='Test Area',  
            is_active=True    
        )

        self.transaction = Transaction.objects.create(
            customer=self.user_account,
            branch=self.branch, 
            reference='TEST123',
            amount=500.0
        )

        self.product1 = Product.objects.create(
            name='Product 1', 
            description='Test Product 1',
            recommended_retail_price=120,
            image='product1_image_url'
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            description='Test Product 2',
            recommended_retail_price=60,
            image='product2_image_url'
        )
        self.product3 = Product.objects.create(
            name='Product 3', 
            description='Test Product 3',
            recommended_retail_price=400,
            image='product3_image_url'
        )

        self.branch_product1 = BranchProduct.objects.create(
            branch=self.branch, 
            product=self.product1, 
            in_stock=True,
            is_active=True,
            branch_price=100,
            store_reference='BP1',
            created_by=self.user_account
        )
        self.branch_product2 = BranchProduct.objects.create(
            branch=self.branch, 
            product=self.product2, 
            in_stock=False,
            is_active=True,
            branch_price=50,
            store_reference='BP2',
            created_by=self.user_account
        )
        self.branch_product3 = BranchProduct.objects.create(
            branch=self.branch, 
            product=self.product3,
            in_stock=True,
            is_active=False,
            branch_price=350,
            store_reference='BP3',
            created_by=self.user_account
        )

        create_a_sale_campaign(branch_product=self.branch_product1, branch=self.branch)

        self.order = Order.objects.create(
            transaction=self.transaction,
            status=Order.PAYMENT_PENDING,
            delivery=True
        )

        self.ordered_product1 = OrderedProduct.objects.create(
            branch_product=self.branch_product1,
            quantity_ordered=2,
            order_price=self.branch_product1.branch_price,
        )
        self.ordered_product2 = OrderedProduct.objects.create(
            branch_product=self.branch_product2,
            quantity_ordered=1,
            order_price=self.branch_product2.branch_price,
        )
        self.ordered_product3 = OrderedProduct.objects.create(
            branch_product=self.branch_product3,
            quantity_ordered=1,
            order_price=self.branch_product3.branch_price,
        )

        self.order.ordered_products.add(
            self.ordered_product1, self.ordered_product2, self.ordered_product3
        )

    def test_repeat_order_success(self):
        url = reverse('repeat-order', kwargs={'order_id': self.order.id})

        with patch('apps.orders.views.send_mail') as mock_send_mail:
            self.client.force_authenticate(user=self.user)

            response = self.client.get(url)

            mock_send_mail.assert_called_once()

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            data = response.data
            self.assertEqual(data['order_id'], self.order.id)
            self.assertEqual(data['branch']['id'], self.branch.id)

            self.assertEqual(len(data['product_list']), 1)  
            in_stock_product = data['product_list'][0]
            self.assertEqual(in_stock_product['product_id'], self.product1.id)
            self.assertEqual(in_stock_product['quantity_ordered'], 2)
            self.assertEqual(in_stock_product['current_price'], 100)

            self.assertEqual(len(data['out_of_stock']), 1)
            out_of_stock_product = data['out_of_stock'][0]
            self.assertEqual(out_of_stock_product['product_id'], self.product2.id)

            self.assertEqual(data['new_cost'], 'R 200.00')

    def test_repeat_order_not_found(self):

        non_existent_order_id = 9999 
        url = reverse('repeat-order', kwargs={'order_id': non_existent_order_id})

        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('error'), 'Order not found')

    def test_email_sending_failure(self):

        with patch('apps.orders.views.send_mail', side_effect=Exception("Email sending failed")):
            url = reverse('repeat-order', kwargs={'order_id': self.order.id})

            self.client.force_authenticate(user=self.user)

            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to send email", response.data['error'])

    def test_repeat_order_with_no_stock(self):

        self.branch_product1.in_stock = False
        self.branch_product1.save()

        url = reverse('repeat-order', kwargs={'order_id': self.order.id})

        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(len(data['product_list']), 0)

        self.assertEqual(len(data['out_of_stock']), 2)

        self.assertEqual(data['new_cost'], 'R 0.00')

    def test_check_for_order_changes_with_sale_campaign(self):

        order = self.order
        check_for_order_url = reverse(
            "check-for-order-changes", kwargs={"order_id": order.pk}
        )
        response = self.client.get(check_for_order_url)

        pass

    def test_check_for_order_changes_no_sale_campaign(self):

        SaleCampaign.objects.all().delete()

        order = self.order
        check_for_order_url = reverse(
            "check-for-order-changes", kwargs={"order_id": order.pk}
        )
        response = self.client.get(check_for_order_url)

        pass

    def test_check_for_order_changes_branch_price_changes(self):

        SaleCampaign.objects.all().delete()

        self.branch_product1.branch_price = 300.00
        self.branch_product1.save()

        order = self.order
        check_for_order_url = reverse(
            "check-for-order-changes", kwargs={"order_id": order.pk}
        )
        response = self.client.get(check_for_order_url)

        pass

    def test_check_for_order_changes_inactive_products(self):

        self.branch_product1.branch_price = 300.00
        self.branch_product1.save()

        order = self.order
        check_for_order_url = reverse(
            "check-for-order-changes", kwargs={"order_id": order.pk}
        )
        response = self.client.get(check_for_order_url)

        pass

    def test_check_for_order_changes_full_order(self):

        self.branch_product2.in_stock = True
        self.branch_product2.save()

        self.branch_product3.is_active = True
        self.branch_product3.save()

        order = self.order
        check_for_order_url = reverse(
            "check-for-order-changes", kwargs={"order_id": order.pk}
        )
        response = self.client.get(check_for_order_url)

        pass
