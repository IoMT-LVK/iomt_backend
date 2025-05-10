import pandas as pd
import clickhouse_connect
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CH_HOST = 'clickhouse'
CH_USER = 'mqttUser'
CH_PASSWORD = 'resUttqm'
CH_DATABASE = 'IoMT_DB'


def sanitize_mac(mac: str) -> str:
    return mac.replace(':', '_')

def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE
    )

def load_user_data(user_id: str, mac: str, freq: int, days: int = 60):
    try:
        client = get_ch_client()
        
        if not client.command(f"EXISTS TABLE ecg_summary_results"):
            logger.warning("Table ecg_summary_results does not exist")
            return pd.DataFrame(columns=['timestamp', 'bpm'])
            
        query = f"""
        SELECT 
            timestamp,
            bpm
        FROM ecg_summary_results
        WHERE 
            user_id = '{user_id}' AND
            mac = '{mac}' AND
            freq = {freq} AND
            timestamp >= now() - INTERVAL {days} DAY
        ORDER BY timestamp
        """

        result = client.query(query)
        
        if not result.result_rows:
            logger.warning("No data found in summary table")
            return pd.DataFrame(columns=['timestamp', 'bpm'])
        
        df = pd.DataFrame(result.result_rows, columns=['timestamp', 'bpm'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Loaded {len(df)} ECG results from summary table")
        return df
        
    except Exception as e:
        logger.error(f"Error loading ECG summary data: {e}")
        return pd.DataFrame(columns=['timestamp', 'bpm'])

def predict_user_next_session(user_id: str, mac: str, freq: int):
    try:
        # Загрузка данных за последние 60 дней
        df = load_user_data(user_id, mac, freq, days=60)
        
        if df.empty or len(df) < 10:  # Минимум 10 точек для ARIMAX
            logger.warning("Недостаточно данных для прогноза")
            return datetime.now() + timedelta(hours=1)

        # Подготовка данных
        df = df.sort_values('timestamp')
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 60  # в минутах
        df = df.dropna()
        
        data = df.tail(30).copy()
        
        y = data['time_diff'].values
        X = data['bpm'].values.reshape(-1, 1)
        
        y_train, y_test = y[:-1], y[-1]
        X_train, X_test = X[:-1], X[-1]
        
        order = (1, 0, 1)  # (p, d, q)
        
        model = ARIMA(endog=y_train, exog=X_train, order=order)
        model_fit = model.fit()
        
        next_interval = model_fit.forecast(exog=X_test.reshape(1, -1))[0]
        
        #next_interval = max(10, min(next_interval, 24 * 60))
        
        last_time = data['timestamp'].iloc[-1]
        next_session = last_time + timedelta(minutes=next_interval)
        
        min_next_time = datetime.now() + timedelta(minutes=10)
        if next_session < min_next_time:
            next_session = min_next_time
            
        logger.info(f"Прогнозируемое время следующей сессии: {next_session}")
        return next_session

    except Exception as e:
        logger.error(f"Ошибка прогнозирования ARIMAX: {e}")
        return datetime.now() + timedelta(hours=1)