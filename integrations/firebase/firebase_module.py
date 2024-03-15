
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

    # current config is set for developement only:
    def sendNotification(self):
        try:
            device_token = 'cqmGKjazRUS5HfJypYk6r6:APA91bG0D4HYDz-21j2rK3mKP-M7HOAhcxR1_XEDCXUMqB4V_9Jd_1WFIAHq_zIw1o5LTPJUxJk4Xskzd4F1dO_OSk_bx4l48Jcac_KeXbGv5Fwj0aDZ-4-YsTEBvZei3t0dRgmw3yz0'
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Pet Foods has receieved your order!",
                    body="This user has commented"
                ),
                data={
                    'score': '850',
                    'time': '2:45',
                },
                token=device_token,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)
        except Exception as e:
            print(str(e))
            pass