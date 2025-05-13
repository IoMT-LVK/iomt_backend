from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from ecg_processor import process_ecg
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import clickhouse_connect


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'

app = FastAPI(
    title="ECG Processing API",
    description="API for processing ECG data and storing results",
    version="1.0.0"
)

class ECGRequest(BaseModel):
    user_id: str
    mac: str
    freq: int

class ECGResult(BaseModel):
    timestamp: str
    user_id: str
    mac: str
    freq: int
    bpm: float
    session_date: str

def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE
    )

@app.on_event("startup")
async def startup_event():
    try:
        client = get_ch_client()
        client.ping()
        logger.info("Successfully connected to ClickHouse")
    except Exception as e:
        logger.error(f"ClickHouse connection error: {str(e)}")
        raise

@app.post("/process-ecg/", response_model=Dict[str, int])
async def process_ecg_endpoint(request: ECGRequest):
    """
    Обработка данных ЭКГ
    - **user_id**: ID пользователя
    - **mac**: MAC-адрес устройства
    - **freq**: Частота дискретизации ЭКГ (в Гц)
    """
    try:
        bpm = process_ecg(request.user_id, request.mac, request.freq)
        
        if bpm == -1:
            raise HTTPException(
                status_code=424,
                detail="Not enough ECG data available for processing"
            )
        elif bpm == -2:
            raise HTTPException(
                status_code=500,
                detail="ECG processing error"
            )
        
        logger.info(f"Processed ECG for user {request.user_id}: BPM={bpm}")
        return {"bpm": bpm}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/results/", response_model=List[ECGResult])
async def get_results(limit: int = 100):
    """
    Получение последних результатов ЭКГ
    - **limit**: Максимальное количество возвращаемых записей (по умолчанию 100)
    """
    try:
        client = get_ch_client()
        
        query = f"""
        SELECT 
            timestamp,
            user_id,
            mac,
            freq,
            bpm,
            session_date
        FROM ecg_summary_results
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        result = client.query(query)
        
        if not result.result_rows:
            raise HTTPException(
                status_code=404,
                detail="No ECG results found"
            )
        
        return [
            {
                "timestamp": str(row[0]),
                "user_id": row[1],
                "mac": row[2],
                "freq": row[3],
                "bpm": row[4],
                "session_date": str(row[5])
            }
            for row in result.result_rows
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving results"
        )

@app.get("/results/{user_id}", response_model=List[ECGResult])
async def get_user_results(user_id: str, limit: int = 100):
    """
    Получение результатов ЭКГ для конкретного пользователя
    - **user_id**: ID пользователя
    - **limit**: Максимальное количество возвращаемых записей (по умолчанию 100)
    """
    try:
        client = get_ch_client()
        
        query = f"""
        SELECT 
            timestamp,
            user_id,
            mac,
            freq,
            bpm,
            session_date
        FROM ecg_summary_results
        WHERE user_id = '{user_id}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        result = client.query(query)
        
        if not result.result_rows:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for user {user_id}"
            )
            
        return [
            {
                "timestamp": str(row[0]),
                "user_id": row[1],
                "mac": row[2],
                "freq": row[3],
                "bpm": row[4],
                "session_date": str(row[5])
            }
            for row in result.result_rows
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving user results"
        )