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
    """Загружает данные пользователя из таблицы с результатами"""
    try:
        client = get_ch_client()
        
        # Проверяем существование таблицы
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

        print(df)
        
        if df.empty or len(df) < 5:  # Минимум 5 точек для прогноза
            logger.warning("Недостаточно данных для прогноза")
            return datetime.now() + timedelta(hours=1)

        # Создаем временные метки и интервалы
        df = df.sort_values('timestamp')
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 60  # в минутах
        df = df.dropna()
        
        # Используем последние 10 точек для прогноза
        last_points = df.tail(10)
        
        # Простая линейная регрессия для прогноза следующего интервала
        X = np.arange(len(last_points)).reshape(-1, 1)
        y = last_points['time_diff'].values
        
        if len(y) < 2:
            return datetime.now() + timedelta(hours=1)
            
        # Прогнозируем следующий интервал
        next_interval = np.mean(y[-3:])  # Среднее последних 3 интервалов
        
        # Рассчитываем время следующей сессии
        last_time = df['timestamp'].iloc[-1]
        next_session = last_time + timedelta(minutes=next_interval)
        
        # Ограничиваем разумными пределами (не раньше чем через 10 минут)
        min_next_time = datetime.now() + timedelta(minutes=10)
        if next_session < min_next_time:
            next_session = min_next_time
            
        return next_session

    except Exception as e:
        logger.error(f"Ошибка прогнозирования: {e}")
        return datetime.now() + timedelta(hours=1)