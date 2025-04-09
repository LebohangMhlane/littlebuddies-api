import json
from datetime import datetime, timedelta, timezone
from datetime import time

from django.db import models
from django.conf import settings

from cryptography.fernet import Fernet as fernet

from apps.accounts.models import UserAccount
from django.core.exceptions import ValidationError


class MerchantBusiness(models.Model):
    logo = models.CharField(
        max_length=120,
        blank=False,
        null=True,
        help_text="Enter your business logo image/name."
    )
    user_account = models.OneToOneField(
        "accounts.UserAccount",
        on_delete=models.CASCADE,
        help_text="Each business must be linked to a merchant account."
    )
    name = models.CharField(
        max_length=120,
        blank=False,
        help_text="This is the name of your business that customers will see."
    )
    email = models.EmailField(
        max_length=120,
        blank=False,
        help_text="Used for order notifications and customer communication."
    )
    address = models.CharField(
        max_length=120,
        blank=False,
        help_text="Your business address or main operating location."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If unchecked, your business will be hidden from customers."
    )
    delivery_fee = models.DecimalField(
        max_digits=50,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Flat delivery fee that will be charged to customers per order."
    )
    closing_time = models.TimeField(
        default=time(16, 30),
        help_text="Orders will not be accepted after this time."
    )

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
    is_active = models.BooleanField(
        default=False,
        help_text="Enable this branch to allow it to receive orders."
    )
    address = models.CharField(
        max_length=120,
        help_text="Physical location of this branch. Make sure it's clear for deliveries."
    )
    merchant = models.ForeignKey(
        MerchantBusiness,
        on_delete=models.CASCADE,
        null=True,
        help_text="This branch is associated with the selected business."
    )

    class Meta:
        verbose_name = "a branch"
        verbose_name_plural = "My Branches"

    def __str__(self) -> str:
        return f"{self.merchant.name} - {self.address}"


def default_campaign_end_date():
    return datetime.now() + timedelta(days=5)

class SaleCampaign(models.Model):
    active = models.BooleanField(
        default=True,
        help_text="If unchecked, this campaign will not apply any discounts."
    )
    branch = models.ForeignKey(
        Branch,
        blank=False,
        null=True,
        on_delete=models.CASCADE,
        help_text="Select the branch where this discount campaign will apply."
    )
    percentage_off = models.PositiveIntegerField(
        blank=False,
        help_text="Discount percentage to apply on the product price (max 50%)."
    )
    delayed_percentage_off = models.PositiveIntegerField(
        blank=False,
        default=0,
        help_text="Use this to schedule a future discount. It will apply after 24 hours."
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Automatically updated whenever changes are made to this campaign."
    )
    branch_product = models.ForeignKey(
        "products.BranchProduct",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        help_text="Choose the specific product from a branch that this campaign targets."
    )
    campaign_ends = models.DateField(
        default=default_campaign_end_date,
        help_text="Date when the campaign will stop applying discounts."
    )
    campaign_ends = models.DateField(default=default_campaign_end_date)

    class Meta:
        verbose_name = "Sale Campaign"
        verbose_name_plural = "Sale Campaigns"

    def __str__(self) -> str:
        return f"{self.branch}"

    def clean(self):
        if self.percentage_off > 50:
            raise ValidationError({'percentage_off': "Sale campaign discount cannot exceed 50%."})

    def save(self, *args, **kwargs):
        if self.pk:  # if this is an update
            old = SaleCampaign.objects.get(pk=self.pk)
            if old.percentage_off != self.percentage_off:
                self.delayed_percentage_off = self.percentage_off
                self.percentage_off = old.percentage_off
        self.full_clean()
        super(SaleCampaign, self).save(*args, **kwargs)

    # TODO: determine the best time to trigger this method:
    def apply_delayed_changes(self):
        """Call this method to apply pending changes if 24 hours have passed."""
        if self.delayed_percentage_off != self.percentage_off:
            if timezone.now() >= self.last_updated + timedelta(hours=24):
                self.percentage_off = self.delayed_percentage_off
                self.save(update_fields=["percentage_off"])

    def calculate_sale_campaign_price(self):
        # Always calculate based on the current active percentage_off
        branch_price = self.branch_product.branch_price
        return round(branch_price - (branch_price * self.percentage_off / 100), 2)
