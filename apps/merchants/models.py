from typing import Iterable
from django.db import models
from django.conf import settings

from apps.accounts.models import UserAccount
from cryptography.fernet import Fernet as fernet


class Merchant(models.Model):
    user_account = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(max_length=255, blank=False)
    address = models.CharField(max_length=1000, blank=False)
    is_active = models.BooleanField(default=True)
    paygateId = models.CharField(max_length=20, blank=False)
    paygateSecret = models.CharField(max_length=32, blank=False, default="")
    fernetToken = models.CharField(max_length=2000, blank=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.user_account.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.encryptPaygateSecret()
        super(Merchant, self).save(*args, **kwargs)

    def encryptPaygateSecret(self):
        key = settings.FERNET_KEY
        fernet_instance = fernet(key=key)
        token = fernet_instance.encrypt(f"{self.paygateSecret}".encode())
        self.fernetToken = token
        self.paygateSecret = ""

class Product(models.Model):

    is_active = models.BooleanField(default=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, blank=False, null=True)
    name = models.CharField(max_length=200, blank=False, default="")
    description = models.CharField(max_length=200, blank=False, default="")
    original_price = models.PositiveIntegerField(blank=False, default=0)
    in_stock = models.BooleanField(default=True)
    image = models.CharField(max_length=800, blank=False, default="")
    store_reference = models.CharField(max_length=200, blank=False, default="")
    discount_percentage = models.PositiveIntegerField(blank=False, default=0)

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"
    
    def save(self) -> None:
        return super().save()

class TransactionHistory(models.Model):
    pass