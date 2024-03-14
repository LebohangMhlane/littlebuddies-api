from django.db import models
from django.contrib.auth.models import User
# from django.dispatch import receiver
# from django.db.models.signals import post_save

class UserAccount(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=255, blank=False)
    phone_number = models.PositiveIntegerField(blank=False, null=True, unique=True)
    is_merchant = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username}'s - User Account"


class UserAccountSettings(models.Model):
    pass