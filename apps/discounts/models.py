from django.db import models
from django.contrib.auth.models import User
from apps.accounts.models import UserAccount
import uuid

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    referred_email = models.EmailField()
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.code} - {self.user.email}"
