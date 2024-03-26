

import os
from django.conf import settings
import firebase_admin


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