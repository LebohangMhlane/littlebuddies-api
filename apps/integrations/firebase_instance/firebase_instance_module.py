
import datetime
from firebase_admin import messaging

from apps.transactions.models import Transaction


class FirebaseInstance():

    def sendNotification(self, updatedTransaction:Transaction):
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


