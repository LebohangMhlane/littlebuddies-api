from django.db import models

from apps.transactions.models import Transaction


class Order(models.Model):

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    orderStatuses = {
        PENDING: "PENDING",
        COMPLETED: "COMPLETED",
        CANCELLED: "CANCELLED",
    }

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    status = models.CharField(max_length=9, choices=orderStatuses, default=PENDING)
    created = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.transaction.customer.user.first_name}{self.transaction.customer.user.last_name} from {self.transaction.merchant.name}"

