from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from apps.accounts.models import UserAccount
from .models import Voucher
from global_test_config.global_test_config import GlobalTestCaseConfig

class ReferralVoucherTests(GlobalTestCaseConfig, TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        
        # Create test user
        create_account_url = reverse("create_account_view")
        self.userInputData = {
            "username": "TestUser0621837747",
            "password": "TestPass123",
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com",
            "address": "123 Test Street",
            "phoneNumber": "0621837747",
            "deviceToken": "test-device-token",
            "isMerchant": False,
        }
        
        response = self.client.post(
            path=create_account_url,
            data=self.userInputData,
            format='json'
        )
        
        user_id = response.data['userAccount']['user']['id']
        self.user = User.objects.get(id=user_id)
        self.user_account = UserAccount.objects.get(id=response.data['userAccount']['id'])
        
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_refer_friend_successful(self):
        refer_url = reverse("refer-friend")
        referral_data = {
            "friend_email": "friend@example.com"
        }
        
        with patch('apps.discounts.views.send_mail') as mock_send_mail:
            response = self.client.post(
                refer_url,
                data=referral_data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data["success"])
            self.assertIn("voucher_code", response.data)
            
            voucher = Voucher.objects.first()
            self.assertIsNotNone(voucher)
            self.assertEqual(voucher.referred_email, referral_data["friend_email"])
            self.assertEqual(voucher.user, self.user_account)
            self.assertFalse(voucher.is_claimed)
            
            mock_send_mail.assert_called_once()

    def test_refer_friend_unauthorized(self):
        self.client.credentials()  
        refer_url = reverse("refer-friend")
        referral_data = {
            "friend_email": "friend@example.com"
        }
        
        response = self.client.post(
            refer_url,
            data=referral_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_claim_voucher_successful(self):
        refer_url = reverse("refer-friend")
        referral_data = {
            "friend_email": "friend@example.com"
        }
        
        with patch('apps.discounts.views.send_mail'):
            self.client.post(
                refer_url,
                data=referral_data,
                format='json'
            )
        
        voucher = Voucher.objects.first()
        claim_url = reverse("claim-voucher")
        claim_data = {
            "voucher_code": voucher.code
        }
        
        response = self.client.post(
            claim_url,
            data=claim_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        voucher.refresh_from_db()
        self.assertTrue(voucher.is_claimed)

    def test_claim_invalid_voucher(self):
        claim_url = reverse("claim-voucher")
        claim_data = {
            "voucher_code": "INVALID123"
        }
        
        response = self.client.post(
            claim_url,
            data=claim_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid or expired voucher code")