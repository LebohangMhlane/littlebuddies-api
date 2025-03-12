from django.db import models

from apps.accounts.models import UserAccount
from apps.merchants.models import Branch


class Transaction(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("FAILED", "Failed"),
        ("DECLINED", "Declined"),
        ("NOT_DONE", "Not Done"),
        ("RECEIVED_BY_PAYGATE", "Received by PayGate"),
        ("SETTLEMENT_VOIDED", "Settlement Voided"),
        ("CUSTOMER_CANCELLED", "Customer Cancelled"),
    ]

    reference = models.CharField(max_length=191, blank=False, null=True)
    customer = models.ForeignKey(
        "accounts.UserAccount", on_delete=models.CASCADE, blank=False
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=False)
    products_ordered = models.ManyToManyField("orders.OrderedProduct", blank=True)
    total_with_service_fee = models.DecimalField(
        blank=False, max_digits=6, decimal_places=2
    )
    total_minus_service_fee = models.DecimalField(
        blank=False, max_digits=6, decimal_places=2
    )
    payment = models.ForeignKey("paystack.Payment", on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING")
    created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        customer_name = (
            f"{self.customer.user.first_name} {self.customer.user.last_name}"
        )
        branch_name = self.branch.merchant.name if self.branch else "Unknown Branch"
        return f"{customer_name} to {branch_name} - reference: {self.reference}"

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)

    def get_transaction_status(self):
        return self.status


class TransactionHistory(models.Model):

    customer = models.ForeignKey(UserAccount, blank=True, on_delete=models.CASCADE)

    pass
