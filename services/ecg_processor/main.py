from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from ecg_processor import process_ecg
import sqlite3
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ECG Processing API",
    description="API for processing ECG data and storing results",
    version="1.0.0"
)

class ECGRequest(BaseModel):
    user_id: str
    mac: str
    freq: int  # Изменили на int, так как частота должна быть числом

class ECGResult(BaseModel):
    id: int
    user_id: str
    mac: str
    freq: int
    bpm: int
    created_at: str

def get_db_connection():
    conn = sqlite3.connect('/db/ecg.db')
    conn.row_factory = sqlite3.Row  # Для доступа к полям по имени
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ecg_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mac TEXT NOT NULL,
                freq INTEGER NOT NULL,
                bpm INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/process-ecg/", response_model=Dict[str, int])
async def process_ecg_endpoint(request: ECGRequest):
    """
    - **user_id**: ID пользователя
    - **mac**: MAC-адрес устройства
    - **freq**: Частота дискретизации ЭКГ (в Гц)
    """
    conn = None 
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
        
        # Сохранение в SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ecg_results (user_id, mac, freq, bpm) VALUES (?, ?, ?, ?)",
            (request.user_id, request.mac, request.freq, bpm)
        )
        conn.commit()
        logger.info(f"Saved ECG result for user {request.user_id}: BPM={bpm}")
        
        return {"bpm": bpm}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    finally:
        if conn is not None:
            conn.close()

@app.get("/results/", response_model=List[ECGResult])
async def get_results(limit: int = 100):
    """
    - **limit**: Максимальное количество возвращаемых записей
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ecg_results ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving results"
        )
    finally:
        conn.close()

@app.get("/results/{user_id}", response_model=List[ECGResult])
async def get_user_results(user_id: str, limit: int = 100):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM ecg_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?""",
            (user_id, limit)
        )
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No results found for this user"
            )
            
        return [dict(row) for row in results]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving user results"
        )
    finally:
        conn.close()