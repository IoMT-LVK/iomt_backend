import pandas as pd
import clickhouse_connect
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima
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
        df = load_user_data(user_id, mac, freq, days=60)
        print(df)
        
        if df.empty or len(df) < 10:
            logger.warning("Недостаточно данных для прогноза")
            print(datetime.now())
            return datetime.now() + timedelta(hours=24)

        df = df.sort_values('timestamp')
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600
        df = df.dropna()
        
        order = (1, 1, 1)  # (p, d, q)
        y = df['time_diff'].values
        X = df[['bpm']].values
        
        model = ARIMA(endog=y, exog=X, order=order)
        model_fit = model.fit()
        
        logger.info(f"Параметры модели ARIMAX{order}:")
        logger.info(model_fit.summary())
        
        next_interval = model_fit.forecast(steps=1, exog=X[-1].reshape(1, -1))[0]
        
        next_session = df['timestamp'].iloc[-1] + timedelta(hours=next_interval)
        
        min_next_time = datetime.now() + timedelta(hours=8)
        return max(next_session, min_next_time)
        
    except Exception as e:
        logger.error(f"Ошибка прогнозирования ARIMAX: {e}", exc_info=True)
        return datetime.now() + timedelta(hours=24)
