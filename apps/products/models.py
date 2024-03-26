from django.db import models

from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness

class Product(models.Model):

    isActive = models.BooleanField(default=False)
    merchant = models.ForeignKey(MerchantBusiness, on_delete=models.CASCADE, blank=False, null=True)
    name = models.CharField(max_length=200, blank=False, default="")
    description = models.CharField(max_length=200, blank=False, default="")
    originalPrice = models.PositiveIntegerField(blank=False, default=0)
    inStock = models.BooleanField(default=True)
    image = models.CharField(max_length=800, blank=False, default="")
    storeReference = models.CharField(max_length=200, blank=False, default="")
    discountPercentage = models.PositiveIntegerField(blank=False, default=0)
    createdBy = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"