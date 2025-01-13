from django.db import models
from django.contrib.auth.models import User


class UserAccount(models.Model): 

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=191, blank=True, unique=False)
    phone_number = models.PositiveIntegerField(blank=False, null=True, unique=True)
    phone_number_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    is_merchant = models.BooleanField(default=False)
    device_token = models.CharField(max_length=191, blank=False, unique=False)
    can_create_merchants = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password_change_date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username}'s - User Account"

    def save(self, *args, **kwargs):
        self.is_active = self.user.is_active
        super(UserAccount, self).save(*args, **kwargs)

class AccountSetting(models.Model):

    user_account = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False, null=True)
    full_name = models.CharField(max_length=191, blank=False, null=True)
    num_of_orders_placed = models.PositiveBigIntegerField(blank=True, null=True)
    num_of_orders_fulfilled = models.PositiveBigIntegerField(blank=True, null=True)
    num_of_orders_cancelled = models.PositiveBigIntegerField(blank=True, null=True)
    fav_store = models.ForeignKey("merchants.MerchantBusiness", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}'s settings"


class DataRequest(models.Model):
    user_account = models.ForeignKey(UserAccount, null=True, blank=False, on_delete=models.CASCADE)
    date_requested = models.DateField(auto_now=True)

    def __str__(self):
        return self.user_account.user.get_full_name()
