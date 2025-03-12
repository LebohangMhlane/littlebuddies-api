from django.db import models

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch


class GlobalProduct(models.Model):

    name = models.CharField(max_length=191, blank=False, default="")
    description = models.TextField(max_length=191, blank=False, default="")
    recommended_retail_price = models.PositiveIntegerField(blank=False, default=0)
    image = models.CharField(max_length=191, blank=False, default="")
    photo = models.ImageField(upload_to='photos/%Y/%m/&d', default="")
    category = models.PositiveSmallIntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.name}"


class BranchProduct(models.Model):

    in_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    global_product = models.ForeignKey(GlobalProduct, on_delete=models.CASCADE)
    branch_price = models.DecimalField(blank=False, null=True, decimal_places=2, default=0.00, max_digits=6)
    store_reference = models.CharField(max_length=191, blank=False, default="")
    created_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)

    def __str__(self) -> str:
        return f"{self.branch.merchant.name} - Product {self.global_product.name}"
