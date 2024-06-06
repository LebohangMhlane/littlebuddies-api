import json
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings

from apps.accounts.models import UserAccount
from cryptography.fernet import Fernet as fernet

class MerchantBusiness(models.Model):

    # TODO: find a cleaner way to do this.
    # I anticipate more locations in the future
    Kloof = "Kloof"
    NewGermany = "New Germany"
    Westville = "Westville"
    Pinetown = "Pinetown"
    Hillcrest = "Hillcrest"

    logo = models.CharField(max_length=2000, blank=False, null=True)
    userAccount = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(max_length=255, blank=False)
    address = models.CharField(max_length=1000, blank=False)
    branchAreas = models.TextField(default="[]")
    isActive = models.BooleanField(default=True)
    paygateReference = models.CharField(max_length=1000, blank=False, default="")
    paygateId = models.CharField(max_length=20, blank=False, unique=True)
    paygateSecret = models.CharField(max_length=32, blank=False, null=True)
    fernetToken = models.CharField(max_length=2000, blank=True, unique=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.userAccount.user.username}"
    
    def save(self, *args, **kwargs):
        self.verifyUserAccount(self.userAccount)
        if not self.pk:
            self.encryptPaygateSecret()
        super(MerchantBusiness, self).save(*args, **kwargs)

    def encryptPaygateSecret(self):
        key = settings.FERNET_KEY
        fernet_instance = fernet(key=key)
        token = fernet_instance.encrypt(f"{self.paygateSecret}".encode())
        self.fernetToken = token
        self.paygateSecret = ""
    
    def verifyUserAccount(self, userAccount: UserAccount):
        if not userAccount.isMerchant:
            raise Exception("User account is not a merchant")
        
    def getMerchantSecretKey(self):
        try:
            fernetToken = self.fernetToken.encode('utf-8')[2:-1]
            fernetInstance = fernet(key=settings.FERNET_KEY)
            secret = fernetInstance.decrypt(fernetToken).decode("utf-8")
            return secret
        except Exception as e:
            raise Exception(f"Failed to decrypt token: {str(e)}")

    def getLocationsList(self):
        return [
            self.Kloof,
            self.NewGermany,
            self.Westville,
            self.Pinetown,
            self.Hillcrest
        ]

    def getBranchAreas(self):
        return json.loads(self.branchAreas)
    
    def setBranchAreas(self, areas:list):
        self.branchAreas = json.dumps(areas)

class Branch(models.Model):

    isActive = models.BooleanField(default=False)
    address = models.CharField(max_length=200)
    area = models.CharField(max_length=200, default="")
    merchant = models.ForeignKey(MerchantBusiness, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return f"{self.address}"
    

class SaleCampaign(models.Model):

    branch = models.ForeignKey(Branch, blank=False, null=True, on_delete=models.CASCADE)
    percentageOff = models.PositiveIntegerField()
    branchProducts = models.ManyToManyField("products.BranchProduct")
    campaignEnds = models.DateField(default=datetime.now() + timedelta(days=5))
    
    def __str__(self) -> str:
        return f"{self.branch.merchant.name} - {self.branch.area} - sale campaign"
