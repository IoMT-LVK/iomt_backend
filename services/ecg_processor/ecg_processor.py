from datetime import datetime
import json
import logging
import time
from paho.mqtt import subscribe
from paho.mqtt.client import MQTTv5
import requests
import sys
import traceback
import clickhouse_connect as clickhouse
import numpy as np
import pandas as pd
import sqlite3

# Конфигурация
CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'
SQLITE_DB = '/db/ecg.db'

# Настройка логгера
log = logging.getLogger(__name__)
def configure_logger(logger):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)

def init_sqlite():
    """Инициализация базы данных SQLite"""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ecg_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mac TEXT NOT NULL,
            freq TEXT NOT NULL,
            bpm INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_sqlite(user_id, mac, freq, bpm):
    """Сохранение результатов в SQLite"""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ecg_results (user_id, mac, freq, bpm) VALUES (?, ?, ?, ?)",
        (user_id, mac, freq, bpm)
    )
    conn.commit()
    conn.close()

def get_ecg_data_from_clickhouse(user_id, mac, freq, time_range_min=1):
    try:
        client = clickhouse.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE
        )
        
        # Используем правильные имена столбцов из таблицы
        query = """
        SELECT timestamp, values 
        FROM ecg_data
        ORDER BY timestamp
        """
        
        result = client.query(query)
        
        # Преобразуем данные: берем первый канал ЭКГ (первое значение в массиве)
        data = []
        for row in result.result_rows:
            timestamp, values = row
            if isinstance(values, list) and len(values) > 0:
                data.append((timestamp, values[0]))  # Берем первое значение
        
        df = pd.DataFrame(data, columns=['timestamp', 'value'])
        return df
        
    except Exception as e:
        log.error(f"Error getting data from ClickHouse: {e}")
        raise

# Ваши оригинальные функции алгоритма Пана-Томпкинса
def lpf(x):
    y = x.copy()
    for n in x.index:
        if(n < 13):
            continue
        y.iloc[n,1] = 2*y.iloc[n-1,1] - y.iloc[n-2,1] + x.iloc[n,1] - 2*x.iloc[n-6,1] + x.iloc[n-12,1]
    return y

def hpf(x):
    y = x.copy()
    for n in x.index:
        if(n < 33):
            continue
        y.iloc[n,1] = y.iloc[n-1,1] - x.iloc[n,1]/32 + x.iloc[n-16,1] - x.iloc[n-17,1] + x.iloc[n-32,1]/32
    return y

def deriv(x):
    y = x.copy()
    for n in x.index:
        if(n < 4):
            continue
        y.iloc[n, 1] = (2*x.iloc[n,1] + x.iloc[n-1,1] - x.iloc[n-3,1] - 2*x.iloc[n-4,1])/4
    return y

def squaring(x):
    y = x.copy()
    for n in x.index:
        y.iloc[n,1] = x.iloc[n,1]**2
    return y

def win_sum(x, ws):
    y = x.copy()
    l = int(ws/5)
    for n in x.index:
        tmp_sum = 0
        if(n > 5998-l):
            break
        if(n < l):
            continue
        for j in range(n-l, n+l+1):
            tmp_sum += x.iloc[j,1]
        y.iloc[n,1] = tmp_sum/(l+1)
    return y

def get_peaks(data):
    threshold = 60
    peaks_x = []
    for i in range(1, len(data)-1):
        if data[i] > threshold:
            if (data[i] > data[i-1] and data[i] > data[i+1]):
                peaks_x.append(i)
    peaks_y = [data[index] for index in peaks_x]
    return peaks_x, peaks_y

def process_ecg(user_id, mac, freq):
    """Обрабатывает данные ЭКГ с использованием алгоритма Пана-Томпкинса"""
    try:
        # Получаем данные из ClickHouse (только первый канал)
        ecg_data = get_ecg_data_from_clickhouse(user_id, mac, freq)
        if ecg_data.empty:
            raise ValueError("No ECG data found in ClickHouse")
        
        # Применяем алгоритм Пана-Томпкинса
        f1 = lpf(ecg_data)
        f2 = hpf(f1)
        f3 = deriv(f2)
        f4 = squaring(f3)
        window_size = 22
        f5 = win_sum(f4, window_size)

        # Сглаживание сигнала
        filter_length = 4
        moving_average = np.convolve(f5["value"], np.ones(filter_length), mode="same")
        moving_average /= filter_length

        # Поиск пиков
        peaks_x, peaks_y = get_peaks(moving_average[0:6000])

        # Вычисление BPM
        if len(peaks_x) < 2:
            bpm = 0  # Недостаточно пиков для расчета
        else:
            # Вычисляем средний интервал между пиками в секундах
            timestamps = ecg_data['timestamp'].values
            intervals = np.diff(timestamps[peaks_x].astype(np.int64)) / 1e9
            mean_interval = np.mean(intervals)
            bpm = 60 / mean_interval
        
        # Сохраняем результат в SQLite
        save_to_sqlite(user_id, mac, freq, int(round(bpm)))
        
        return int(round(bpm))
    except Exception as e:
        log.error(f"Error processing ECG: {e}")
        raise