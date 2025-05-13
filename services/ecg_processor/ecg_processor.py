import logging
from datetime import datetime, timedelta
import traceback
import numpy as np
import pandas as pd
import clickhouse_connect
import sqlite3
import re

CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'
SQLITE_DB = '/db/ecg.db'

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE
    )

def sanitize_table_name(mac: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', mac)

def init_sqlite():
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ecg_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                mac TEXT NOT NULL,
                freq INTEGER NOT NULL,
                bpm INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        log.info("SQLite database initialized")
    except Exception as e:
        log.error(f"SQLite init error: {e}")
        raise

def ensure_ecg_table_exists(user_id: str, mac: str, freq: int):
    try:
        client = get_ch_client()
        sanitized_mac = sanitize_table_name(mac)
        table_name = f"{user_id}_{sanitized_mac}_{freq}"
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}`
        (
            timestamp DateTime,
            values Array(Float32)
        ) ENGINE = MergeTree()
        ORDER BY timestamp
        """
        
        client.command(create_table_query)
        log.info(f"Ensured table exists: {table_name}")
        
    except Exception as e:
        log.error(f"Table creation error: {e}")
        raise

def ensure_results_table_exists():
    try:
        client = get_ch_client()
        
        create_summary_table = """
        CREATE TABLE IF NOT EXISTS ecg_summary_results
        (
            timestamp DateTime,
            session_date Date DEFAULT toDate(timestamp),
            user_id String,
            mac String,
            freq Int32,
            bpm Float32
        ) ENGINE = MergeTree()
        ORDER BY (user_id, mac, session_date, timestamp)
        """
        client.command(create_summary_table)
        log.info("Ensured ecg_summary_results table exists")
        
        # Таблица для хранения сырых данных
        create_raw_table = """
        CREATE TABLE IF NOT EXISTS ecg_raw_data
        (
            timestamp DateTime,
            user_id String,
            mac String,
            freq Int32,
            values Array(Float32)
        ) ENGINE = MergeTree()
        ORDER BY (user_id, mac, timestamp)
        """
        client.command(create_raw_table)
        log.info("Ensured ecg_raw_data table exists")
        
    except Exception as e:
        log.error(f"Results table creation error: {e}")
        raise

def get_ecg_data_from_clickhouse(user_id: str, mac: str, freq: int, time_range_min: int = 30):
    """Получение данных ЭКГ из таблицы устройства"""
    try:
        client = get_ch_client()
        sanitized_mac = sanitize_table_name(mac)
        table_name = f"{user_id}_{sanitized_mac}_{freq}"
        
        if not client.command(f"EXISTS TABLE `{table_name}`"):
            log.error(f"Table {table_name} does not exist")
            return pd.DataFrame(columns=['timestamp', 'value'])
        
        time_bounds = client.query(f"""
        SELECT min(timestamp) as min_time, max(timestamp) as max_time 
        FROM `{table_name}`
        """).result_rows[0]
        
        log.info(f"Time bounds in table {table_name}: {time_bounds[0]} to {time_bounds[1]}")
        
        query = f"""
        SELECT timestamp, values 
        FROM `{table_name}`
        ORDER BY timestamp
        """
        
        result = client.query(query)
        
        if not result.result_rows:
            log.warning(f"No data found in table {table_name}")
            return pd.DataFrame(columns=['timestamp', 'value'])
        
        INVERSE_DISCRETE = 16777214.0
        data = [
            (row[0], row[1][0] / INVERSE_DISCRETE if row[1] and len(row[1]) > 0 else 0.0)
            for row in result.result_rows
        ]
        
        df = pd.DataFrame(data, columns=['timestamp', 'value'])
        log.info(f"Retrieved {len(df)} ECG samples from {table_name}")
        return df
        
    except Exception as e:
        log.error(f"ClickHouse error: {e}\n{traceback.format_exc()}")
        return pd.DataFrame(columns=['timestamp', 'value'])

def save_to_sqlite(user_id: str, mac: str, freq: int, bpm: int):
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ecg_results (user_id, mac, freq, bpm) VALUES (?, ?, ?, ?)",
            (user_id, mac, freq, bpm)
        )
        conn.commit()
        conn.close()
        log.info(f"Saved result to SQLite: user={user_id}, bpm={bpm}")
    except Exception as e:
        log.error(f"SQLite save error: {e}")
        raise



def save_to_clickhouse(user_id: str, mac: str, freq: int, bpm: float):
    try:
        client = get_ch_client()
        
        query = """
        INSERT INTO ecg_summary_results 
        (user_id, mac, freq, bpm, timestamp)
        VALUES (%s, %s, %s, %s, now())
        """
        
        client.command(query, [user_id, mac, freq, bpm])
        log.info(f"Saved result to ClickHouse summary: user={user_id}, bpm={bpm}")
        
    except Exception as e:
        log.error(f"ClickHouse save error: {e}")
        raise

# Фильтры обработки сигнала
def lpf(x):
    y = x.copy()
    values = y['value'].values
    for n in range(12, len(values)):
        values[n] = 2*values[n-1] - values[n-2] + x['value'].iloc[n] - 2*x['value'].iloc[n-6] + x['value'].iloc[n-12]
    return y

def hpf(x):
    y = x.copy()
    values = y['value'].values
    for n in range(32, len(values)):
        values[n] = values[n-1] - x['value'].iloc[n]/32 + x['value'].iloc[n-16] - x['value'].iloc[n-17] + x['value'].iloc[n-32]/32
    return y

def deriv(x):
    y = x.copy()
    if len(y) < 5: 
        y['value'] = 0.0
        return y
    
    derivative = np.zeros(len(y))
    
    values = y['value'].values
    derivative[4:-4] = (2*values[4:-4] + values[3:-5] - values[1:-7] - 2*values[:-8]) / 4
    
    y['value'] = derivative
    return y

def squaring(x):
    y = x.copy()
    y['value'] = y['value'] ** 2
    return y

def win_sum(x, window_size=22):
    y = x.copy()
    l = max(1, window_size // 5)
    values = x['value'].values
    window = np.ones(2*l + 1) / (2*l + 1)
    smoothed = np.convolve(values, window, mode='same')
    y['value'] = smoothed
    return y

def get_peaks(signal, fs=200):
    if len(signal) < 10:
        return []
    
    # Адаптивный порог
    median = np.median(signal)
    mad = 1.4826 * np.median(np.abs(signal - median))
    threshold = median + 2 * mad
    
    peaks = []
    min_interval = int(0.3 * fs)
    
    for i in range(1, len(signal)-1):
        if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            if not peaks or (i - peaks[-1]) >= min_interval:
                peaks.append(i)
    

    if len(peaks) < 2:
        threshold = median + 1.5 * mad
        peaks = []
        for i in range(1, len(signal)-1):
            if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                if not peaks or (i - peaks[-1]) >= min_interval:
                    peaks.append(i)
    
    return peaks

def process_ecg(user_id: str, mac: str, freq: int):
    """Обработка ЭКГ с улучшенной обработкой ошибок"""
    try:
        init_sqlite()
        ensure_ecg_table_exists(user_id, mac, freq)
        ensure_results_table_exists()
        
        ecg_data = get_ecg_data_from_clickhouse(user_id, mac, freq)
        
        if len(ecg_data) < 100:
            log.warning(f"Insufficient data samples: {len(ecg_data)} (minimum 100 required)")
            save_to_sqlite(user_id, mac, freq, -1)
            save_to_clickhouse(user_id, mac, freq, -1.0)
            return -1
        
        log.info(f"Processing {len(ecg_data)} samples with freq {freq} Hz")
        
        try:
            filtered = lpf(ecg_data)
            filtered = hpf(filtered)
            filtered = deriv(filtered)
            filtered = squaring(filtered)
            filtered = win_sum(filtered, window_size=int(0.15 * freq))
            
            peaks = get_peaks(filtered['value'].values, fs=freq)
            
            if len(peaks) < 2:
                log.warning(f"Only {len(peaks)} peaks detected (minimum 2 required)")
                bpm = 0
            else:
                intervals = np.diff(ecg_data['timestamp'].iloc[peaks].astype(np.int64)) / 1e9
                valid_intervals = intervals[(intervals > 0.3) & (intervals < 2.0)]
                
                if len(valid_intervals) < 2:
                    log.warning(f"Only {len(valid_intervals)} valid intervals")
                    bpm = 0
                else:
                    bpm = 60 / np.mean(valid_intervals)
                    bpm = np.clip(bpm, 40, 180)
                    log.info(f"Successfully calculated BPM: {bpm}")
        
        except Exception as processing_error:
            log.error(f"Signal processing error: {str(processing_error)}")
            bpm = -2
        
        save_to_sqlite(user_id, mac, freq, int(round(bpm)))
        save_to_clickhouse(user_id, mac, freq, float(bpm))
        
        return int(round(bpm))
        
    except Exception as e:
        log.error(f"ECG processing failed: {e}\n{traceback.format_exc()}")
        save_to_sqlite(user_id, mac, freq, -2)
        save_to_clickhouse(user_id, mac, freq, -2.0)
        raise