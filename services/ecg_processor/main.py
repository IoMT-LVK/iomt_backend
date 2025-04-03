from fastapi import FastAPI
from ecg_processor import process_ecg
import sqlite3
from pydantic import BaseModel

app = FastAPI()

class ECGRequest(BaseModel):
    user_id: str
    mac: str
    freq: str

def init_db():
    """Инициализация базы данных SQLite для хранения результатов"""
    conn = sqlite3.connect('/db/ecg.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ecg_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mac TEXT NOT NULL,
            freq TEXT NOT NULL,
            bpm INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.post("/process-ecg/")
async def process_ecg_endpoint(request: ECGRequest):
    init_db()
    
    # Обработка ЭКГ
    bpm = process_ecg(request.user_id, request.mac, request.freq)
    
    # Сохранение в SQLite
    conn = sqlite3.connect('/db/ecg.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ecg_results (user_id, mac, freq, bpm) VALUES (?, ?, ?, ?)",
        (request.user_id, request.mac, request.freq, bpm)
    )
    conn.commit()
    conn.close()
    
    return {"bpm": bpm}

@app.get("/results/")
async def get_results():
    init_db()
    conn = sqlite3.connect('/db/ecg.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ecg_results ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return {"results": results}