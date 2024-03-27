from django.db import models

from apps.transactions.models import Transaction


class Order(models.Model):

    PENDING_DELIVERY = "PENDING_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    PAYMENT_PENDING = "PAYMENT_PENDING"

    orderStatuses = {
        PENDING_DELIVERY: "PENDING_DELIVERY",
        DELIVERED: "DELIVERED",
        CANCELLED: "CANCELLED",
        PAYMENT_PENDING: "PAYMENT_PENDING"
    }

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=orderStatuses, default=PAYMENT_PENDING)
    created = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    delivery = models.BooleanField(default=True)
    deliveryDate = models.DateField(auto_now=True)
    address = models.CharField(max_length=200, blank=False, null=True)

    def __str__(self) -> str:
        return f"{self.transaction.customer.user.first_name}{self.transaction.customer.user.last_name} from {self.transaction.merchant.name}"

