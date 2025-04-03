from fastapi import FastAPI
from ecg_predictor import predict_next_session

app = FastAPI()

@app.get("/predict-next-session/")
async def get_next_session():
    next_session_time = predict_next_session()
    return {"next_session_time": next_session_time.isoformat()}