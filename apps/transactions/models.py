from django.db import models
# from django.dispatch import receiver
# from django.db.models.signals import post_save


from apps.accounts.models import UserAccount
from apps.merchants.models import MerchantBusiness
from apps.products.models import Product


class Transaction(models.Model):

    payRequestId = models.CharField(max_length=36, blank=False, null=True)
    reference = models.CharField(max_length=255, blank=False, null=True)
    customer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)
    merchant = models.ForeignKey(MerchantBusiness, on_delete=models.CASCADE)
    productsPurchased = models.ManyToManyField(Product, blank=True)
    numberOfProducts = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=0, blank=False)
    discountTotal = models.PositiveIntegerField(default=0, blank=False)
    completed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    notDone = models.BooleanField(default=False)
    receievedByPaygate = models.BooleanField(default=False)
    settlementVoided = models.BooleanField(default=False)
    userCancelled = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True)
    dateCompleted = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.customer.user.first_name} {self.customer.user.last_name} to {self.merchant.name}"

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)

    # TODO: use an enum for these later:
    def getTransactionStatus(self):
        possibleStatuses = {
            "Transaction Completed": self.completed,
            "Transaction Cancelled": self.cancelled,
            "Transaction Failed": self.failed,
            "Transaction Declined": self.declined,
            "Not Done": self.notDone,
            "Recieved By Paygate": self.receievedByPaygate,
            "Settlement Voided": self.settlementVoided,
            "Customer Cancelled": self.userCancelled,
        }
        currentStatus = [key for key, value in possibleStatuses.items() if value is True]
        return currentStatus[0]


class TransactionHistory(models.Model):

    customer = models.ForeignKey(UserAccount, blank=True, on_delete=models.CASCADE)

    pass