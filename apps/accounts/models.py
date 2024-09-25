from django.db import models
from django.utils import timezone
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
    password_change_date = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.user.username}'s - User Account"
    
    def save(self, *args, **kwargs):
        self.isActive = self.user.is_active
        super(UserAccount, self).save(*args, **kwargs)


class AccountSettings(models.Model):
    pass