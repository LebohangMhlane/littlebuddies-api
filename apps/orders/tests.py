from unittest.mock import patch
from django.test import TestCase
from rest_framework.reverse import reverse
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from django.core import mail

from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderedProduct
from global_test_config.global_test_config import GlobalTestCaseConfig, MockedPaygateResponse
from apps.transactions.models import Transaction
from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness, Branch
from apps.products.models import Product, BranchProduct
from .serializers import OrderSerializer

User = get_user_model()

class OrderTests(GlobalTestCaseConfig, TestCase):

    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_create_order(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        authToken = self.loginAsCustomer()
        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)
        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)
        branch = merchant.branch_set.all().first()
        checkoutFormPayload = {
            "branchId": str(merchant.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        _ = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {authToken}",
        )
        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        response = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )
        order = Order.objects.all().first()
        products = order.transaction.productsPurchased.filter(id__in=[p1.id, p2.id])
        self.assertEqual(products[0].id, p1.id)
        self.assertEqual(order.transaction.branch.id, int(checkoutFormPayload["branchId"]))
        self.assertEqual(order.status, Order.PENDING_DELIVERY)
        self.assertEqual(order.transaction.customer.id, customer.id)


    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_get_all_orders_as_customer(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        customerAuthToken = self.loginAsCustomer()

        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)

        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiatePaymentResponse = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}",
        )

        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        paymentNotificatonResponse = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )

        getAllOrdersUrl = reverse("get_all_orders_view")
        getAllOrdersResponse = self.client.get(
            getAllOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}"
        )
        order = Order.objects.all().first()
        orderFromResponse = getAllOrdersResponse.data["orders"][0]
        self.assertEqual(
            orderFromResponse["id"], order.id
        )
        self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            orderFromResponse["transaction"]["branch"]["id"], 
            int(checkoutFormPayload["branchId"]))
        self.assertEqual(
            float(orderFromResponse["transaction"]["amount"]), 
            float(checkoutFormPayload["totalCheckoutAmount"])
        )


    @patch("apps.integrations.firebase_integration.firebase_module.FirebaseInstance.sendTransactionStatusNotification")
    @patch("apps.paygate.views.PaymentInitializationView.sendInitiatePaymentRequestToPaygate")
    def test_get_all_orders_as_merchant(self, mockedResponse, mockedSendNotification):

        mockedResponse.return_value = MockedPaygateResponse()

        customer = self.createTestCustomer()
        customerAuthToken = self.loginAsCustomer()

        merchantUserAccount = self.createMerchantUserAccount()
        merchant = self.createMerchantBusiness(merchantUserAccount)

        p1 = self.createProduct(merchant, merchantUserAccount, "Bob's dog food", 200)
        p2 = self.createProduct(merchant, merchantUserAccount, "Bob's cat food", 100)

        branch = merchant.branch_set.all().first()

        checkoutFormPayload = {
            "branchId": str(branch.pk),
            "totalCheckoutAmount": "300.0",
            "products": "[{'id': 1, 'quantityOrdered': 1}, {'id': 2, 'quantityOrdered': 2}]",
            "discountTotal": "0",
            "delivery": True,
            "deliveryDate": self.makeDate(1),
            "address": "71 downthe street Bergville"
        }
        initiate_payment_url = reverse("initiate_payment_view")
        initiatePaymentResponse = self.client.post(
            initiate_payment_url,
            data=checkoutFormPayload,
            HTTP_AUTHORIZATION=f"Token {customerAuthToken}",
        )

        paymentNotificationResponse = "PAYGATE_ID=10011072130&PAY_REQUEST_ID=23B785AE-C96C-32AF-4879-D2C9363DB6E8&REFERENCE=pgtest_123456789&TRANSACTION_STATUS=1&RESULT_CODE=990017&AUTH_CODE=5T8A0Z&CURRENCY=ZAR&AMOUNT=3299&RESULT_DESC=Auth+Done&TRANSACTION_ID=78705178&RISK_INDICATOR=AX&PAY_METHOD=CC&PAY_METHOD_DETAIL=Visa&CHECKSUM=f57ccf051307d8d0a0743b31ea379aa1"
        paymentNotificationUrl = reverse("payment_notification_view")
        paymentNotificatonResponse = self.client.post(
            paymentNotificationUrl,
            data=paymentNotificationResponse,
            content_type='application/x-www-form-urlencoded'
        )

        merchantAuthToken = self.loginAsMerchant()

        getAllOrdersUrl = reverse("get_all_orders_view")
        getAllOrdersResponse = self.client.get(
            getAllOrdersUrl,
            HTTP_AUTHORIZATION=f"Token {merchantAuthToken}"
        )
        order = Order.objects.all().first()
        orderFromResponse = getAllOrdersResponse.data["orders"][0]
        self.assertEqual(
            orderFromResponse["id"], order.id
        )
        self.assertEqual(orderFromResponse["transaction"]["id"], order.transaction.id)
        self.assertEqual(
            orderFromResponse["transaction"]["branch"]["id"], 
            int(checkoutFormPayload["branchId"]))
        self.assertEqual(
            float(orderFromResponse["transaction"]["amount"]), 
            float(checkoutFormPayload["totalCheckoutAmount"])
        )

class CancelOrderTests(TestCase):
    def setUp(self):
        # Create a consistent test setup
        self.client = APIClient()

        # Create user accounts
        self.customer_user = User.objects.create_user(
            username="test_customer", 
            email="customer@example.com",
            password="testpassword123"
        )
        self.customer_account = UserAccount.objects.create(
            user=self.customer_user,
            phoneNumber=1234567890,
            deviceToken='test_device_token_1'
        )

        self.another_customer_user = User.objects.create_user(
            username="another_customer", 
            email="another_customer@example.com",
            password="testpassword123"
        )
        self.another_customer_account = UserAccount.objects.create(
            user=self.another_customer_user,
            phoneNumber=9876543210,
            deviceToken='test_device_token_2'
        )

        # Create merchant setup
        self.merchant_user = User.objects.create_user(
            username="merchant", 
            email="merchant@example.com",
            password="merchantpassword123"
        )
        self.merchant_account = UserAccount.objects.create(
            user=self.merchant_user,
            phoneNumber=5555555555,
            deviceToken='merchant_device_token'
        )

        self.merchant_business = MerchantBusiness.objects.create(
            userAccount=self.merchant_account,
            name="Test Merchant Business",
            email="merchant@example.com"
        )

        self.branch = Branch.objects.create(
            merchant_business=self.merchant_business,
            name="Test Branch"
        )

        # Create transactions
        self.customer_transaction = Transaction.objects.create(
            customer=self.customer_account,
            branch=self.branch
        )

        # Create orders for testing
        self.pending_order = Order.objects.create(
            transaction=self.customer_transaction,
            status=Order.PENDING,
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

        # URL for cancelling orders
        self.cancel_order_url = reverse('cancel-order')

    def _authenticate_customer(self, user=None):
        """Helper method to authenticate a customer"""
        user = user or self.customer_user
        self.client.force_authenticate(user=user)

    def test_cancel_order_success(self):
        """Test successful order cancellation"""
        self._authenticate_customer()
        
        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success', False))
        self.assertEqual(response.data.get('message'), "Order cancelled successfully!")

        # Refresh order from database
        self.pending_order.refresh_from_db()
        self.assertEqual(self.pending_order.status, Order.CANCELLED)
        self.assertFalse(self.pending_order.acknowledged)

    def test_cancel_order_unauthenticated(self):
        """Test order cancellation by unauthenticated user"""
        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_order_different_customer(self):
        """Test order cancellation by different customer"""
        self._authenticate_customer(user=self.another_customer_user)
        
        payload = {"order_id": self.pending_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_order_missing_order_id(self):
        """Test order cancellation with missing order ID"""
        self._authenticate_customer()
        
        payload = {}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(response.data.get('message'), "Order ID is required!")

    def test_cancel_order_invalid_order_id(self):
        """Test order cancellation with invalid order ID"""
        self._authenticate_customer()
        
        payload = {"order_id": 99999}  # Non-existent ID
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_already_cancelled_order(self):
        """Test cancelling an already cancelled order"""
        self._authenticate_customer()
        
        payload = {"order_id": self.cancelled_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(
            response.data.get('message'), 
            "Order cannot be cancelled at this stage."
        )

    def test_cancel_delivered_order(self):
        """Test cancelling a delivered order"""
        self._authenticate_customer()
        
        payload = {"order_id": self.delivered_order.id}
        response = self.client.post(self.cancel_order_url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data.get('success', False))
        self.assertEqual(
            response.data.get('message'), 
            "Order cannot be cancelled at this stage."
        )


class RepeatOrderViewTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.client = APIClient()
        
        # Create a user
        self.user = User.objects.create_user(
            username='testuser', 
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Create a user account
        self.user_account = UserAccount.objects.create(
            user=self.user, 
            phoneNumber=1234567890
        )
        
        # Create a merchant 
        self.merchant = MerchantBusiness.objects.create(
            userAccount=self.user_account,
            name='Test Merchant', 
            logo='merchant_logo_url'
        )
        
        # Create a branch
        self.branch = Branch.objects.create(
            merchant_business=self.merchant,
            name='Test Branch', 
            address='123 Test St'
        )
        
        # Create a transaction
        self.transaction = Transaction.objects.create(
            customer=self.user_account,
            branch=self.branch, 
            reference='TEST123'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='Product 1', 
            description='Test Product 1',
            recommendedRetailPrice=120,
            image='product1_image_url'
        )
        self.product2 = Product.objects.create(
            name='Product 2', 
            description='Test Product 2',
            recommendedRetailPrice=60,
            image='product2_image_url'
        )
        
        # Create branch products
        self.branch_product1 = BranchProduct.objects.create(
            branch=self.branch, 
            product=self.product1, 
            inStock=True,
            isActive=True,
            branchPrice=100,
            storeReference='BP1',
            createdBy=self.user_account
        )
        self.branch_product2 = BranchProduct.objects.create(
            branch=self.branch, 
            product=self.product2, 
            inStock=False,
            isActive=True,
            branchPrice=50,
            storeReference='BP2',
            createdBy=self.user_account
        )
        
        # Create the original order
        self.order = Order.objects.create(
            transaction=self.transaction, 
            status=Order.PAYMENT_PENDING,
            delivery=True
        )
        
        # Create ordered products
        self.ordered_product1 = OrderedProduct.objects.create(
            branchProduct=self.branch_product1, 
            quantityOrdered=2
        )
        self.ordered_product2 = OrderedProduct.objects.create(
            branchProduct=self.branch_product2, 
            quantityOrdered=1
        )
        
        # Add ordered products to the order
        self.order.orderedProducts.add(self.ordered_product1, self.ordered_product2)

    def test_repeat_order_success(self):
        """
        Test successful repeat order retrieval
        """
        url = reverse('repeat-order', kwargs={'order_id': self.order.id})
        
        with patch('django.core.mail.send_mail') as mock_send_mail:
            # Authenticate the user
            self.client.force_authenticate(user=self.user)
            
            response = self.client.get(url)
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response data
        data = response.data
        self.assertEqual(data['order_id'], self.order.id)
        self.assertEqual(data['branch']['id'], self.branch.id)
        
        # Check product list
        self.assertEqual(len(data['product_list']), 1)  # Only in-stock product
        in_stock_product = data['product_list'][0]
        self.assertEqual(in_stock_product['product_id'], self.product1.id)
        self.assertEqual(in_stock_product['quantity_ordered'], 2)
        self.assertEqual(in_stock_product['current_price'], 100)
        
        # Check out of stock products
        self.assertEqual(len(data['out_of_stock']), 1)
        out_of_stock_product = data['out_of_stock'][0]
        self.assertEqual(out_of_stock_product['product_id'], self.product2.id)
        
        # Check new cost calculation
        self.assertEqual(data['new_cost'], 'R 200.00')
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        
    def test_repeat_order_not_found(self):
        """
        Test retrieving a non-existent order
        """
        non_existent_order_id = 9999  # Assume this ID doesn't exist
        url = reverse('repeat-order', kwargs={'order_id': non_existent_order_id})
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(url)
        
        # Check response status and error message
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('error'), 'Order not found')
    
    def test_email_sending_failure(self):
        """
        Test handling of email sending failure
        """
        # Patch send_mail to raise an exception
        with patch('django.core.mail.send_mail', side_effect=Exception('SMTP Error')):
            url = reverse('repeat-order', kwargs={'order_id': self.order.id})
            
            # Authenticate the user
            self.client.force_authenticate(user=self.user)
            
            response = self.client.get(url)
        
        # Check response status for email failure
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data.get('error'), 'Failed to send email')
    
    def test_repeat_order_with_no_stock(self):
        """
        Test repeat order with all products out of stock
        """
        # Set all branch products to out of stock
        self.branch_product1.inStock = False
        self.branch_product1.save()
        
        url = reverse('repeat-order', kwargs={'order_id': self.order.id})
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(url)
        
        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify no in-stock products
        data = response.data
        self.assertEqual(len(data['product_list']), 0)
        
        # Verify both products are out of stock
        self.assertEqual(len(data['out_of_stock']), 2)
        
        # Check new cost calculation
        self.assertEqual(data['new_cost'], 'R 0.00')