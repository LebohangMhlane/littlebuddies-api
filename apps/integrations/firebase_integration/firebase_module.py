import datetime
from firebase_admin import messaging

from apps.orders.models import Order
from apps.transactions.models import Transaction
from global_utils import GlobalUtils


class FirebaseInstance(GlobalUtils):

    def send_transaction_status_notification(self, transaction: Transaction):
        try:
            transactionStatus = transaction.get_transaction_status()
            if transaction.status == "COMPLETED":
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=f"Order from {transaction.branch.merchant.name} successfully placed!",
                        body="You will receive another notification when the store has acknowleged your order.",
                    ),
                    data={
                        "transactionStatus": transactionStatus,
                        "time": str(datetime.datetime.now()),
                    },
                    token=transaction.customer.device_token,
                )
                _ = messaging.send(message)
                self.logger.info("Notification sent to customer")
            self.logger.info(
                f"Transaction status is: {transactionStatus}. Notification not sent to customer."
            )
            return True
        except Exception as e:
            self.logger.info(
                f"Failed to send notification to customer. Error: {str(e)}"
            )
            return False

    def sendOrderAcknowledgementNotification(self, order: Order):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"{order.transaction.merchant.name} has acknowlegded your order!",
                    body="You will receive your order soon.",
                ),
                data={},
                token=order.transaction.customer.device_token,
            )
            _ = messaging.send(message)
            return True
        except Exception as e:
            pass
