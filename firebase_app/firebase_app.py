import os
from django.conf import settings

import firebase_admin
from firebase_admin import messaging


class FirebaseApp():
    
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

    def send_push_notification(self, token, title, body, data=None):
        """
        Send a push notification to a specific device using Firebase Cloud Messaging (FCM).

        :param token: The FCM device token of the recipient.
        :param title: Title of the notification.
        :param body: Body text of the notification.
        :param data: (Optional) Dictionary of additional data.
        """
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data if data else {},  # Custom data payload
            token=token,  # Device token
        )

        try:
            response = messaging.send(message)
            print(f"Notification sent successfully: {response}")
            return response
        except Exception as e:
            print(f"Error sending notification: {e}")
            return None
