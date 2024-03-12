from django.db import models

from accounts.models import UserAccount


class Merchant(models.Model):

    user_account = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(max_length=255, blank=False)
    address = models.CharField(max_length=1000, blank=False)
    paygate_id = models.CharField(max_length=20, blank=False)
    reference_number = models.CharField(max_length=10, blank=False)

class Product(models.Model):
    pass

class TransactionHistory(models.Model):
    pass