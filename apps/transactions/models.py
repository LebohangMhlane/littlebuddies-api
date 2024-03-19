from django.db import models

from apps.accounts.models import UserAccount
from apps.merchants.models import Merchant
from apps.products.models import Product



class Transaction(models.Model):

    customer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    productsPurchased = models.ManyToManyField(Product, blank=False)
    totalAmountPaid = models.PositiveIntegerField(default=0, blank=False)
    discountTotal = models.PositiveIntegerField(default=0, blank=False)
    completed = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True)
    dateCompleted = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.customer.user.first_name} {self.customer.user.last_name} to {self.merchant.name}"


class TransactionHistory(models.Model):

    customer = models.ForeignKey(UserAccount, blank=True, on_delete=models.CASCADE)

    pass