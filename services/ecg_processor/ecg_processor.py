import logging
from datetime import datetime, timedelta
import traceback
import numpy as np
import pandas as pd
import clickhouse_connect
import sqlite3
import re

# Конфигурация ClickHouse
CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'
SQLITE_DB = '/db/ecg.db'

# Настройка логгера
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

def sanitize_table_name(mac: str) -> str:
    """Очистка MAC-адреса для использования в имени таблицы"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', mac)

def init_sqlite():
    """Инициализация SQLite"""
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
    """Проверка и создание таблицы для устройства, если её нет"""
    try:
        client = clickhouse_connect.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE
        )
        
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

def get_ecg_data_from_clickhouse(user_id: str, mac: str, freq: int, time_range_min: int = 1):
    """Получение данных ЭКГ из таблицы устройства"""
    try:
        client = clickhouse_connect.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE
        )
        
        sanitized_mac = sanitize_table_name(mac)
        table_name = f"{user_id}_{sanitized_mac}_{freq}"
        
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_range_min)
        
        query = f"""
        SELECT timestamp, values 
        FROM `{table_name}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp
        """
        
        result = client.query(query)
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
        raise

def save_to_sqlite(user_id: str, mac: str, freq: int, bpm: int):
    """Сохранение результатов в SQLite"""
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


# Оптимизированные фильтры с векторизованными операциями
def lpf(x):
    """Оптимизированный низкочастотный фильтр"""
    y = x.copy()
    values = y['value'].values
    for n in range(12, len(values)):
        values[n] = 2*values[n-1] - values[n-2] + x['value'].iloc[n] - 2*x['value'].iloc[n-6] + x['value'].iloc[n-12]
    return y

def hpf(x):
    """Оптимизированный высокочастотный фильтр"""
    y = x.copy()
    values = y['value'].values
    for n in range(32, len(values)):
        values[n] = values[n-1] - x['value'].iloc[n]/32 + x['value'].iloc[n-16] - x['value'].iloc[n-17] + x['value'].iloc[n-32]/32
    return y

def deriv(x):
    """Векторизованный дифференциатор"""
    y = x.copy()
    values = y['value'].values
    values[4:] = (2*x['value'].iloc[4:] + x['value'].iloc[3:-1] - x['value'].iloc[1:-3] - 2*x['value'].iloc[:-4]) / 4
    return y

def squaring(x):
    """Векторизованное возведение в квадрат"""
    y = x.copy()
    y['value'] = y['value'] ** 2
    return y

def win_sum(x, window_size=22):
    """Оптимизированное скользящее окно с обработкой краёв"""
    y = x.copy()
    l = max(1, window_size // 5)
    values = x['value'].values
    window = np.ones(2*l + 1) / (2*l + 1)
    
    # Используем convolution с mode='same' для правильной обработки краёв
    smoothed = np.convolve(values, window, mode='same')
    y['value'] = smoothed
    return y

def get_peaks(signal, fs=200):
    """Улучшенная детекция пиков с адаптивным порогом"""
    # 1. Расчет адаптивного порога
    median = np.median(signal)
    mad = 1.4826 * np.median(np.abs(signal - median))  # Median Absolute Deviation
    threshold = median + 3 * mad  # Более надежный порог
    
    # 2. Поиск пиков
    peaks = []
    for i in range(1, len(signal)-1):
        if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            peaks.append(i)
    
    # 3. Отбраковка ложных пиков (минимальный интервал = 200 мс)
    min_interval = int(0.2 * fs)  # 200 мс в samples
    cleaned_peaks = []
    prev_peak = -min_interval
    for peak in peaks:
        if peak - prev_peak >= min_interval:
            cleaned_peaks.append(peak)
            prev_peak = peak
    
    return cleaned_peaks

def process_ecg(user_id: str, mac: str, freq: int):
    """Обработка ЭКГ с улучшенной обработкой ошибок"""
    try:
        # Инициализация компонентов
        init_sqlite()
        ensure_ecg_table_exists(user_id, mac, freq)
        
        # Получение данных
        ecg_data = get_ecg_data_from_clickhouse(user_id, mac, freq)
        if len(ecg_data) < 1000:
            raise ValueError(f"Insufficient data: only {len(ecg_data)} samples")
        
        # Обработка сигнала
        filtered = lpf(ecg_data)
        filtered = hpf(filtered)
        filtered = deriv(filtered)
        filtered = squaring(filtered)
        filtered = win_sum(filtered, window_size=int(0.15 * freq))
        
        # Детекция пиков
        peaks = get_peaks(filtered['value'].values, fs=freq)
        
        # Расчет ЧСС
        if len(peaks) < 2:
            bpm = 0
            log.warning("Not enough peaks detected")
        else:
            intervals = np.diff(ecg_data['timestamp'].iloc[peaks].astype(np.int64)) / 1e9
            valid_intervals = intervals[(intervals > 0.3) & (intervals < 2.0)]
            
            if len(valid_intervals) < 2:
                raise ValueError("Invalid RR intervals")
            
            bpm = 60 / np.mean(valid_intervals)
            bpm = np.clip(bpm, 40, 180)
        
        # Сохранение результата
        save_to_sqlite(user_id, mac, freq, int(round(bpm)))
        return int(round(bpm))
        
    except Exception as e:
        log.error(f"ECG processing failed: {e}\n{traceback.format_exc()}")
        save_to_sqlite(user_id, mac, freq, 0)  # Сохраняем 0 при ошибке
        raise