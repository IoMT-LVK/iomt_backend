from fastapi import FastAPI
from ecg_predictor import predict_user_next_session
from pydantic import BaseModel

app = FastAPI()

class PredictRequest(BaseModel):
    user_id: str
    mac: str
    freq: int

@app.post("/predict-next-session/")
async def get_next_session(request: PredictRequest):
    next_session_time = predict_user_next_session(
        request.user_id,
        request.mac,
        request.freq
    )
    return {"next_session_time": next_session_time.isoformat()}