import datetime
from django.db import models
from django.utils import timezone

from apps.merchants.models import SaleCampaign
from apps.transactions.models import Transaction
from apps.products.models import BranchProduct, GlobalProduct
from apps.accounts.models import UserAccount

def setDate():
    todaysDate = datetime.datetime.now()
    todaysDate = todaysDate.strftime("%Y-%m-%d %H:%M:%S")
    return todaysDate

class Order(models.Model):

    PENDING_PICKUP = "PENDING_PICKUP"
    PENDING_DELIVERY = "PENDING_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    PAYMENT_PENDING = "PAYMENT_PENDING"

    order_statuses = {
        PENDING_DELIVERY: "PENDING_DELIVERY",
        DELIVERED: "DELIVERED",
        CANCELLED: "CANCELLED",
        PAYMENT_PENDING: "PAYMENT_PENDING"
    }

    # TODO: convert model to fit the one in the mobile app:
    customer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="customer", blank=False, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True)
    products_ordered = models.ManyToManyField("orders.OrderedProduct", related_name="ordered_products")
    status = models.CharField(max_length=16, choices=order_statuses, default=PAYMENT_PENDING)
    created = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    delivery = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)
    delivery_date = models.CharField(max_length=100, blank=False, null=True, default=setDate)
    delivery_address = models.CharField(max_length=191, blank=False, null=True)

    def __str__(self) -> str:
        return f"{self.transaction.customer.user.first_name}{self.transaction.customer.user.last_name} from {self.transaction.branch.merchant.name} - {self.transaction.reference}"


class OrderedProduct(models.Model):

    branch_product = models.ForeignKey(BranchProduct, on_delete=models.CASCADE, blank=False, null=True)
    sale_campaign = models.ForeignKey(SaleCampaign, on_delete=models.CASCADE, blank=True, null=True)
    quantity_ordered = models.PositiveIntegerField()
    order_price = models.DecimalField(
        null=True, blank=False, decimal_places=2, max_digits=10, default=0.00
    )

    def __str__(self) -> str:
        return f"{self.branch_product.global_product.name} - {self.quantity_ordered}"

class CancelledOrder(models.Model):
    CANCELLATION_REASONS = [
        ('CUSTOMER_REQUEST', 'Customer Requested'),
        ('OUT_OF_STOCK', 'Items Out of Stock'),
        ('DELIVERY_ISSUES', 'Delivery Issues'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('OTHER', 'Other'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='cancellations', null=True)
    cancelled_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True)
    cancelled_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=50, choices=CANCELLATION_REASONS)
    additional_notes = models.TextField(blank=True)
    refund_initiated = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-cancelled_at']
        
    def __str__(self):
        return f"Order #{self.order.id} cancelled on {self.cancelled_at}"
    
    @property
    def cancellation_duration(self):
        return self.cancelled_at - self.order.created_at

def record_cancellation(order, user_account, reason='CUSTOMER_REQUEST', notes='', refund_amount=None):
    cancellation = CancelledOrder.objects.create(
        order=order,
        cancelled_by=user_account,
        reason=reason,
        additional_notes=notes,
        refund_amount=refund_amount,
        refund_initiated=bool(refund_amount)
    )
    return cancellation
