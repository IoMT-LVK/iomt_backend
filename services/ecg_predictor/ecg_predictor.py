import pandas as pd
import clickhouse_connect
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация ClickHouse
CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'


def sanitize_mac(mac: str) -> str:
    """Преобразует MAC-адрес в формат, подходящий для имени таблицы"""
    return mac.replace(':', '_')

def get_ch_client():
    """Возвращает клиент ClickHouse"""
    return clickhouse_connect.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE
    )

def load_user_data(user_id: str, mac: str, freq: int, days: int = 60):
    """Загружает данные пользователя из таблицы устройства"""
    try:
        client = get_ch_client()
        table_name = f"{user_id}_{sanitize_mac(mac)}_{freq}"
        
        query = f"""
        SELECT 
            timestamp,
            values[1] as value  # Извлекаем первое значение из массива
        FROM `{table_name}`
        WHERE timestamp >= now() - INTERVAL {days} DAY
        ORDER BY timestamp
        """

        result = client.query(query)
        df = pd.DataFrame(result.result_rows, columns=['timestamp', 'value'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Loaded {len(df)} ECG samples from {table_name}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading ECG data: {e}")
        return pd.DataFrame()

def predict_user_next_session(user_id: str, mac: str, freq: int):
    try:
        # Загрузка данных за 60 дней
        df = load_user_data(user_id, mac, freq, days=60)
        print(df)
        
        if df.empty:
            logger.warning("Недостаточно данных")
            return datetime.now() + timedelta(hours=1)

        # Подготовка данных для ARIMAX
        df["time_diff_min"] = df["timestamp"].diff().dt.total_seconds() / 60
        df = df.dropna(subset=["time_diff_min", "bpm"])
        
        exog = df[["bpm"]].values  # Экзогенная переменная (пульс)
        y = df["time_diff_min"].values  # Интервалы между замерами

        # Обучение ARIMAX
        model = ARIMA(
            endog=y,
            exog=exog,
            order=(2, 1, 1) 
        )
        model_fit = model.fit()

        last_bpm = df["bpm"].iloc[-1]
        forecast_diff = model_fit.forecast(steps=1, exog=[last_bpm])
        next_session = df["timestamp"].iloc[-1] + timedelta(minutes=forecast_diff[0])

        return next_session

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return datetime.now() + timedelta(hours=1)