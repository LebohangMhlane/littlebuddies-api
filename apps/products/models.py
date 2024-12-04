from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch


class Product(models.Model):

    name = models.CharField(max_length=200, blank=False, default="")
    description = models.TextField(max_length=2000, blank=False, default="")
    recommended_retail_price = models.PositiveIntegerField(blank=False, default=0)
    image = models.CharField(max_length=800, blank=False, default="")
    category = models.PositiveSmallIntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.name}"
    

class BranchProduct(models.Model):

    in_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    merchant_name = models.CharField(max_length=250, null=True, blank=True)
    merchant_logo = models.CharField(max_length=300, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch_price = models.FloatField(blank=False, null=True)
    store_reference = models.CharField(max_length=200, blank=False, default="")
    created_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)

    def __str__(self) -> str:
        return f"{self.branch.merchant.name} - Product {self.product.name}"
    
    @receiver(pre_save, sender="products.BranchProduct")
    def update_merchant_name(instance, **kwargs):
        instance.merchant_name = instance.branch.merchant.name
        instance.merchant_logo = instance.branch.merchant.logo