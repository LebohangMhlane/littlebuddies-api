from django.db import models
# from django.dispatch import receiver
# from django.db.models.signals import post_save

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch, MerchantBusiness


class Transaction(models.Model):

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    DECLINED = "DECLINED"
    NOT_DONE = "NOT_DONE"
    RECEIVED_BY_PAYGATE = "RECEIVED_BY_PAYGATE"
    SETTLEMENT_VOIDED = "SETTLEMENT_VOIDED"
    CUSTOMER_CANCELLED = "CUSTOMER_CANCELLED"

    payRequestId = models.CharField(max_length=36, blank=False, null=True)
    reference = models.CharField(max_length=255, blank=False, null=True)
    customer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=False)
    productsPurchased = models.ManyToManyField("orders.OrderedProduct", blank=True)
    numberOfProducts = models.PositiveIntegerField(default=0)
    amount = models.CharField(default="0.00", max_length=7, blank=False)
    discountTotal = models.PositiveIntegerField(default=0, blank=False)
    status = models.CharField(max_length=50, blank=False, default=PENDING)
    dateCreated = models.DateTimeField(auto_now_add=True)
    dateCompleted = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        customer_name = (
            f"{self.customer.user.first_name} {self.customer.user.last_name}"
        )
        branch_name = self.branch.merchant.name if self.branch else "Unknown Branch"
        return f"{customer_name} to {branch_name} - reference: {self.reference}"

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)

    def getTransactionStatus(self):
        return self.status


class TransactionHistory(models.Model):

    customer = models.ForeignKey(UserAccount, blank=True, on_delete=models.CASCADE)

    pass
