from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import UserAccount
from merchants.models import Merchant

# Create your tests here.


class MerchantTests(TestCase):

    def test_create_merchant(self):

        user = User.objects.create(
            username = "Lebohang",
            password = "password"
        )

        user_account = UserAccount.objects.get(user=user)
        
        merchant = Merchant()
        merchant.name = "My Food Store"
        merchant.user_account = user_account
        merchant.paygate_secret = "secret"
        merchant.save()
        
        print(merchant)