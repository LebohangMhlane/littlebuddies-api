from django.db import models

from apps.accounts.models import UserAccount


class Product(models.Model):

    isActive = models.BooleanField(default=False)
    name = models.CharField(max_length=200, blank=False, default="")
    description = models.CharField(max_length=2000, blank=False, default="")
    originalPrice = models.PositiveIntegerField(blank=False, default=0)
    inStock = models.BooleanField(default=True)
    image = models.CharField(max_length=800, blank=False, default="")
    storeReference = models.CharField(max_length=200, blank=False, default="")
    discountPercentage = models.PositiveIntegerField(blank=False, default=0)
    createdBy = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)
    onSpecial = models.BooleanField(default=False)
    category = models.PositiveSmallIntegerField(default=1)
    specialEndDate = models.DateTimeField(auto_now=True) # TODO: fix special ending date issue

    def __str__(self) -> str:
        return f"{self.name}"
    

