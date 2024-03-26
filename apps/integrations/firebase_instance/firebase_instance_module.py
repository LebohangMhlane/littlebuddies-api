
import datetime
from firebase_admin import messaging

from apps.orders.models import Order
from apps.transactions.models import Transaction


class FirebaseInstance():

    def sendTransactionStatusNotification(self, updatedTransaction:Transaction):
        try:
            deviceToken = updatedTransaction.customer.deviceToken
            transactionStatus = updatedTransaction.getTransactionStatus()
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Order from {updatedTransaction.merchant.name} successfully placed!",
                    body="You will receive another notification when the store has acknowleged your order."
                ) if updatedTransaction.completed else messaging.Notification(
                    title=f"Order from {updatedTransaction.merchant.name} failed.",
                    body=f"Reason: {transactionStatus}"
                ),
                data={
                    'transactionStatus': transactionStatus,
                    'time': str(datetime.datetime.now()),
                },
                token=deviceToken,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)
            return True
        except Exception as e:
            print(str(e))
            pass

    def sendOrderAcknowledgementNotification(self, order:Order):
        try:
            deviceToken = order.transaction.customer.deviceToken
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"{order.transaction.merchant.name} has acknowlegded your order!",
                    body="You will receive your order soon."
                ),
                data={},
                token=deviceToken,
            )
            response = messaging.send(message)
            print('Successfully sent acknowledgement notification:', response)
            return True
        except Exception as e:
            pass

