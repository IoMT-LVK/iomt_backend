from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ecg_predictor import predict_user_next_session
from fcm_service import FCMService
import os
from datetime import datetime

app = FastAPI()

FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '/app/credentials/serviceAccountKey.json')
FCMService.initialize(FIREBASE_CREDENTIALS_PATH)

class PredictRequest(BaseModel):
    user_id: str
    mac: str
    freq: int
    device_token: str

@app.post("/predict-next-session/")
async def get_next_session(request: PredictRequest):
    try:
        next_session_time = predict_user_next_session(
            request.user_id,
            request.mac,
            request.freq
        )

        formatted_time = next_session_time.strftime("%d.%m.%Y %H:%M")

        FCMService.send_prediction_notification(
            device_token=request.device_token,
            user_id=request.user_id,
            next_session_time=formatted_time
        )
        print(3)
        return {
            "next_session_time": next_session_time.isoformat(),
            "notification_sent": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))