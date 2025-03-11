from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def order_saved_handler(sender, instance:Order, created, **kwargs):
    """
    Signal triggered after an Order instance is saved.

    :param sender: The model class that triggered the signal.
    :param instance: The actual instance being saved.
    :param created: Boolean, True if a new record was created.
    :param kwargs: Additional arguments.
    """
    if created:
        # runs when the order is first created:
        pass
    else:
        # runs when the order is updated:
        if (
            instance.id
            and instance.acknowledged
            and not instance.acknowledgement_notification_sent
        ):
            # send a notification to the customer:
            settings.FIREBASE_APP.send_push_notification(
                instance.customer.device_token,
                f"{instance.transaction.branch.merchant.name} has acknowledged your order!",
                "It's on it's way soon!",
                {"test": "data sent via notification"},
            )
