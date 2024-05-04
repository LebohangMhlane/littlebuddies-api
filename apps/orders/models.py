import datetime
from django.db import models

from apps.transactions.models import Transaction
from apps.products.models import Product

def setDate():
    todaysDate = datetime.datetime.now()
    todaysDate = todaysDate.strftime()
    return todaysDate

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

    # TODO: convert model to fit the one in the mobile app:
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    orderedProducts = models.ManyToManyField("orders.OrderedProduct", related_name="orderedProducts")
    status = models.CharField(max_length=16, choices=orderStatuses, default=PAYMENT_PENDING)
    created = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    delivery = models.BooleanField(default=True)
    # opted not to use djangos datetime field. Datetime objects will be handled and converted on the mobile app:
    deliveryDate = models.CharField(max_length=100, blank=False, null=True, default=setDate)
    address = models.CharField(max_length=200, blank=False, null=True)

    def __str__(self) -> str:
        return f"{self.transaction.customer.user.first_name}{self.transaction.customer.user.last_name} from {self.transaction.merchant.name} - {self.transaction.reference}"


class OrderedProduct(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=False)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, blank=True, null=True)
    quantityOrdered = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.product.name} - {self.quantityOrdered} - {self.order.transaction.reference}"