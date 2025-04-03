import pandas as pd
import sqlite3
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(user_id=None, mac=None, freq=None):
    """Загружает данные из SQLite с возможностью фильтрации"""
    try:
        logger.info("Загрузка данных из SQLite...")
        conn = sqlite3.connect('/db/ecg.db')
        
        query = "SELECT created_at, bpm FROM ecg_results"
        params = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
            if mac:
                query += " AND mac = ?"
                params.append(mac)
                if freq:
                    query += " AND freq = ?"
                    params.append(freq)
        
        query += " ORDER BY created_at"
        
        df = pd.read_sql(query, conn, parse_dates=['created_at'], params=params)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        raise


def predict_next_session():
    """Предсказывает время следующего сеанса."""
    try:
        df = load_data()

        if df.empty:
            logger.warning("Нет данных для предсказания.")
            raise ValueError("Нет данных для предсказания.")

        if df['bpm'].isnull().any() or np.isinf(df['bpm']).any():
            logger.warning("Обнаружены некорректные данные (NaN или inf). Очистка данных.")
            df = df.dropna(subset=['bpm'])
            df = df[~np.isinf(df['bpm'])]

        if df.empty:
            logger.error("Нет корректных данных для предсказания после очистки.")
            raise ValueError("Нет корректных данных для предсказания.")

        logger.info("Подготовка данных для ARIMA...")
        df = df.set_index('created_at')
        df = df.resample('1min').ffill()

        logger.info("Построение модели ARIMA...")
        model = ARIMA(df['bpm'], order=(1, 1, 1))
        model_fit = model.fit()

        logger.info("Прогнозирование следующего значения...")
        forecast = model_fit.forecast(steps=1)
        next_bpm = forecast[0]

        logger.info("Предсказание времени следующего сеанса...")
        last_time = df.index[-1]
        next_session_time = last_time + timedelta(minutes=30)

        return next_session_time
    except Exception as e:
        logger.error(f"Ошибка при предсказании следующего сеанса: {e}")
        raise