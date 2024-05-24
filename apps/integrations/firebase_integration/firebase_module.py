
import datetime
from firebase_admin import messaging

from apps.orders.models import Order
from apps.transactions.models import Transaction


class FirebaseInstance():

    def sendTransactionStatusNotification(self, transaction:Transaction):
        try:
            transactionStatus = transaction.getTransactionStatus()
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Order from {transaction.merchant.name} successfully placed!",
                    body="You will receive another notification when the store has acknowleged your order."
                ) if transaction.status == transaction.COMPLETED else messaging.Notification(
                    title=f"Order from {transaction.merchant.name} failed.",
                    body=f"Reason: {transactionStatus}"
                ),
                data={
                    'transactionStatus': transactionStatus,
                    'time': str(datetime.datetime.now()),
                },
                token = transaction.customer.deviceToken,
            )
            _ = messaging.send(message)
            return True
        except Exception as e:
            return False

    def sendOrderAcknowledgementNotification(self, order:Order):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"{order.transaction.merchant.name} has acknowlegded your order!",
                    body="You will receive your order soon."
                ),
                data={},
                token = order.transaction.customer.deviceToken,
            )
            _ = messaging.send(message)
            return True
        except Exception as e:
            pass

