from django.db import models
from django.conf import settings

from apps.accounts.models import UserAccount
from cryptography.fernet import Fernet as fernet


class Merchant(models.Model):
    userAccount = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(max_length=255, blank=False)
    address = models.CharField(max_length=1000, blank=False)
    isActive = models.BooleanField(default=True)
    paygateReference = models.CharField(max_length=1000, blank=False, default="")
    paygateId = models.CharField(max_length=20, blank=False)
    paygateSecret = models.CharField(max_length=32, blank=False, default="")
    fernetToken = models.CharField(max_length=2000, blank=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.userAccount.user.username}"
    
    def save(self, *args, **kwargs):
        self.verifyUserAccount(self.userAccount)
        if not self.pk:
            self.encryptPaygateSecret()
        super(Merchant, self).save(*args, **kwargs)

    def encryptPaygateSecret(self):
        key = settings.FERNET_KEY
        fernet_instance = fernet(key=key)
        token = fernet_instance.encrypt(f"{self.paygateSecret}".encode())
        self.fernetToken = token
        self.paygateSecret = ""
    
    def verifyUserAccount(self, userAccount: UserAccount):
        if not userAccount.isMerchant:
            raise Exception("User account is not a merchant")


