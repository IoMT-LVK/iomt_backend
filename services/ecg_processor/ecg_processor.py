import numpy as np
import pandas as pd
import scipy.signal as sig
from scipy.signal import find_peaks
import clickhouse_connect as clickhouse
from datetime import datetime, timedelta
import logging

# Конфигурация ClickHouse
CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'


def get_ecg_data_from_clickhouse(user_id, mac, freq, time_range_min=1):
    """Получает данные ЭКГ из ClickHouse за последние time_range_min минут"""
    try:
        client = clickhouse.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE
        )
        
        table_name = f"{user_id}/{mac}/{freq}"
        query = f"""
        SELECT timestamp, value 
        FROM `{table_name}`
        WHERE timestamp >= now() - INTERVAL {time_range_min} MINUTE
        ORDER BY timestamp
        """
        
        result = client.query(query)
        df = pd.DataFrame(result.result_rows, columns=['timestamp', 'value'])
        return df
    except Exception as e:
        logging.error(f"Error getting data from ClickHouse: {e}")
        raise

def process_ecg(user_id, mac, freq):
    """Обрабатывает данные ЭКГ из ClickHouse и возвращает BPM"""
    try:
        # Получаем данные из ClickHouse
        ecg_data = get_ecg_data_from_clickhouse(user_id, mac, freq)
        if ecg_data.empty:
            raise ValueError("No ECG data found in ClickHouse")
        
        # Применение фильтров
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
        BPM = len(peaks_x)
        return BPM
    except Exception as e:
        logging.error(f"Error processing ECG: {e}")
        raise

# Функции фильтров и обработки сигнала
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