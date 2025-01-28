import json
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings

from cryptography.fernet import Fernet as fernet

from apps.accounts.models import UserAccount

class MerchantBusiness(models.Model):

    # TODO: find a cleaner way to do this.
    # I anticipate more locations in the future
    kloof = "Kloof"
    new_germany = "New Germany"
    westville = "Westville"
    pinetown = "Pinetown"
    hillcrest = "Hillcrest"
    durban_central = "Durban Central"

    logo = models.CharField(max_length=120, blank=False, null=True)
    user_account = models.OneToOneField("accounts.UserAccount", on_delete=models.CASCADE)
    name = models.CharField(max_length=120, blank=False)
    email = models.EmailField(max_length=120, blank=False)
    address = models.CharField(max_length=120, blank=False)
    is_active = models.BooleanField(default=True)
    paygate_reference = models.CharField(max_length=120, blank=False, default="")
    paygate_id = models.CharField(max_length=20, blank=False, unique=True)
    paygate_secret = models.CharField(max_length=32, blank=False, null=True)
    fernet_token = models.CharField(max_length=120, blank=True, unique=True)
    delivery_fee = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.user_account.user.username}"

    def save(self, *args, **kwargs):
        self.verify_user_account(self.user_account)
        if not self.pk:
            self.encrypt_paygate_secret()
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

    def get_merchant_secret_key(self):
        try:
            fernetToken = self.fernet_token.encode('utf-8')[2:-1]
            fernetInstance = fernet(key=settings.FERNET_KEY)
            secret = fernetInstance.decrypt(fernetToken).decode("utf-8")
            return secret
        except Exception as e:
            raise Exception(f"Failed to decrypt token: {str(e)}")

    def get_areas_list(self):
        return [
            self.kloof,
            self.new_germany,
            self.westville,
            self.pinetown,
            self.hillcrest,
            self.durban_central,
        ]

    def get_branch_areas(self):
        return json.loads(self.branch_address)

    def set_branch_areas(self, areas:list):
        self.branch_address = json.dumps(areas)


class Branch(models.Model):

    is_active = models.BooleanField(default=False)
    address = models.CharField(max_length=120)
    area = models.CharField(max_length=120, default="")
    merchant = models.ForeignKey(MerchantBusiness, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return f"{self.merchant.name} - {self.address}"

def default_campaign_end_date():
    return datetime.now() + timedelta(days=5)

class SaleCampaign(models.Model):

    active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, blank=False, null=True, on_delete=models.CASCADE)
    percentage_off = models.PositiveIntegerField()
    branch_product = models.ForeignKey("products.BranchProduct", on_delete=models.CASCADE, null=True, blank=True)
    campaign_ends = models.DateField(default=default_campaign_end_date)

    def __str__(self) -> str:
        return f"{self.branch.merchant.name} - {self.branch.area} - sale campaign"

    def calculate_sale_campaign_price(self):
        branch_price = self.branch_product.branch_price
        return branch_price - (branch_price * self.percentage_off / 100)
