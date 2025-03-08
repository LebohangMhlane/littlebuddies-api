import json
from datetime import datetime, timedelta
from datetime import time

from django.db import models
from django.conf import settings

from cryptography.fernet import Fernet as fernet

from apps.accounts.models import UserAccount

class MerchantBusiness(models.Model):

    logo = models.CharField(max_length=120, blank=False, null=True)
    user_account = models.OneToOneField("accounts.UserAccount", on_delete=models.CASCADE)
    name = models.CharField(max_length=120, blank=False)
    email = models.EmailField(max_length=120, blank=False)
    address = models.CharField(max_length=120, blank=False)
    is_active = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)
    closing_time = models.TimeField(default=time(16, 30))

    class Meta:
        verbose_name = "a business"
        verbose_name_plural = "My Business"

    def __str__(self) -> str:
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.verify_user_account(self.user_account)
        super(MerchantBusiness, self).save(*args, **kwargs)

    def encrypt_paygate_secret(self):
        key = settings.FERNET_KEY
        fernet_instance = fernet(key=key)
        token = fernet_instance.encrypt(f"{self.paygate_secret}".encode())
        self.fernet_token = token
        self.paygate_secret = ""

    def verify_user_account(self, user_account: UserAccount):
        if not user_account.is_merchant:
            raise Exception("User account is not a merchant")


class Branch(models.Model):

    is_active = models.BooleanField(default=False)
    address = models.CharField(max_length=120)
    merchant = models.ForeignKey(MerchantBusiness, on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = "a branch"
        verbose_name_plural = "My Branches"

    def __str__(self) -> str:
        return f"{self.merchant.name} - {self.address}"


def default_campaign_end_date():
    return datetime.now() + timedelta(days=5)

class SaleCampaign(models.Model):

    active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, blank=False, null=True, on_delete=models.CASCADE)
    percentage_off = models.PositiveIntegerField(blank=False)
    branch_product = models.ForeignKey(
        "products.BranchProduct",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    campaign_ends = models.DateField(default=default_campaign_end_date)

    class Meta:
        verbose_name = "Sale Campaign"
        verbose_name_plural = "Sale Campaigns"

    def __str__(self) -> str:
        return f"{self.branch.merchant.name} - {self.branch} - sale campaign"

    def calculate_sale_campaign_price(self):
        branch_price = self.branch_product.branch_price
        return branch_price - (branch_price * self.percentage_off / 100)
