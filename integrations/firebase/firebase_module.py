
import datetime
import os
from django.conf import settings
import firebase_admin
from firebase_admin import messaging

class FirebaseInstance():
    
    def __init__(self):
        credentials = firebase_admin.credentials.Certificate(
            os.path.join(
                settings.BASE_DIR,
                "littlebuddies-d51b7-firebase-adminsdk-kn9jb-35200ca990.json"
            )
        )   
        firebase_admin.initialize_app(
            credential=credentials, 
            options={"projectId": "littlebuddies-d51b7"}
        )

    def sendNotification(self, merchant, customer, payRequestId):
        try:
            deviceToken = customer.deviceToken
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Order from {merchant.name} successfully placed!",
                    body="You will receive another notification when the store has acknowleged your order."
                ),
                data={
                    'payRequestId': str(payRequestId),
                    'time': str(datetime.datetime.now()),
                },
                token=deviceToken,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)
        except Exception as e:
            print(str(e))
            pass