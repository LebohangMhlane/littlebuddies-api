from django.db import models
from django.contrib.auth.models import User


class UserAccount(models.Model): 

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, unique=False)
    phoneNumber = models.PositiveIntegerField(blank=False, null=True, unique=True)
    phoneNumberVerified = models.BooleanField(default=False)
    emailVerified = models.BooleanField(default=False)
    isMerchant = models.BooleanField(default=False)
    deviceToken = models.CharField(max_length=1000, blank=False, unique=False)
    canCreateMerchants = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    password_change_date = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username}'s - User Account"
    
    def save(self, *args, **kwargs):
        self.isActive = self.user.is_active
        super(UserAccount, self).save(*args, **kwargs)

class AccountSetting(models.Model):

    user_account = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False, null=True)
    full_name = models.CharField(max_length=300, blank=False, null=True)
    num_of_orders_placed = models.PositiveBigIntegerField(blank=True, null=True)
    num_of_orders_fulfilled = models.PositiveBigIntegerField(blank=True, null=True)
    fav_store = models.ForeignKey("merchants.MerchantBusiness", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}'s settings"
    

class DataRequest(models.Model):
    user_account = models.ForeignKey(UserAccount, null=True, blank=False, on_delete=models.CASCADE)
    date_requested = models.DateField(auto_now=True)

    def __str__(self):
        return self.user_account.user.get_full_name()