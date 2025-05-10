import firebase_admin
from firebase_admin import credentials, messaging
import logging

logger = logging.getLogger(__name__)

class FCMService:
    _initialized = False

    @classmethod
    def initialize(cls, credential_path):
        if not cls._initialized:
            cred = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase app initialized")

    @classmethod
    def send_prediction_notification(cls, device_token: str, user_id: str, next_session_time: str):
        if not cls._initialized:
            raise RuntimeError("Firebase app not initialized")
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="IoMT Health Center",
                body=f"Следующий сеанс ЭКГ запланирован на {next_session_time}",
            ),
            token=device_token,
            data={
                "type": "ecg_prediction",
                "user_id": user_id,
                "next_session": next_session_time
            }
        )
        
        try:
            response = messaging.send(message)
            logger.info(f"Successfully sent FCM message: {response}")
            return True
        except Exception as e:
            logger.error(f"Error sending FCM message: {e}")
            return False