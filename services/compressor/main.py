from typing import Union
import ctypes
from datetime import datetime
import traceback
import logging
import sys
import pickle
import os

from pydantic import BaseModel
from fastapi import FastAPI, Response, BackgroundTasks
from fastapi.responses import FileResponse
import clickhouse_connect as clickhouse
import numpy as np
import pandas as pd

from generate_cheb import generate


API_USERNAME = "mqttUser"
API_PASSWORD = "resUttqm"
CH_HOST = 'clickhouse'
CH_USER = API_USERNAME
CH_PASSWORD = API_PASSWORD
CH_DATABASE = 'IoMT_DB'
CH_TABLENAME_FORMAT = '{user_id}/{mac}/{freq}'
CH_SESSIONS_FORMAT = 'sessions_{user_id}/{mac}/{freq}'
BUFFER_TABLENAME_FORMAT = '{user_id}/{mac}/{freq}_buffer'
N = 8
M = 1
CHANNEL_NUM = 2

chebyshev_matrix = generate(N)

ls = []
for arr in chebyshev_matrix:
    ls.extend(arr)
chebyshev_list = ls

f = ctypes.CDLL("./libtest.so").solve_c
f.restype = ctypes.POINTER(ctypes.c_double)
f.argtypes = (ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_double),ctypes.c_int,ctypes.c_int)
numbers_array = ctypes.c_double * N
chebyshev_array = ctypes.c_double * (N * N)

class User(BaseModel):
    user_id: int
    mac: str
    freq: int

logger = logging.getLogger(__name__)
def configure_logger(logger):
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(name)-12s [%(asctime)s] %(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)
configure_logger(logger)

app = FastAPI()

def clear_file(file_: str):
    os.unlink(file_)

@app.post("/compress")
def compress(user: User, start_time: str, end_time: str):
    try:
        table = CH_TABLENAME_FORMAT.format(
            user_id=user.user_id,
            mac=user.mac,
            freq=user.freq
        )
        buffer = BUFFER_TABLENAME_FORMAT.format(
            user_id=user.user_id,
            mac=user.mac,
            freq=user.freq
        )
        clh_client = clickhouse.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE,
            client_name=CH_USER,
        )
        clh_client.command(
            """
            CREATE TABLE IF NOT EXISTS {table_name:Identifier} 
            (timestamp DateTime64 CODEC(DoubleDelta, LZ4), lead_1 Float32 CODEC(FPC, LZ4), lead_2 Float32 CODEC(FPC, LZ4))
            Engine MergeTree
            ORDER BY timestamp
            """,
            parameters=dict(table_name=table),
        )
        res = clh_client.query(f"""SELECT * FROM `{buffer}` WHERE timestamp >= '{start_time}' AND timestamp <= '{end_time}' ORDER BY timestamp""")
        record = np.array(res.result_columns)
        perc = 0.2
        measures = len(record[1, :])
        reconstructed = []
        cutoff = False
        reconstructed.append(record[0, :].tolist())
        for lead in range(CHANNEL_NUM):
            reconstructed.append([])
            for batch_i in range(0, measures, N):
                slice_ = record[lead+1, batch_i:batch_i+N].copy()
                if batch_i + N > measures:
                    cutoff = True
                    slice_ = np.append(slice_, [0] * (batch_i + N - measures))
                min_1 = slice_.min()
                max_1 = slice_.max()
                if abs(min_1 - max_1) > perc:
                    currM = N
                else:
                    currM = M
                numbers = numbers_array(*list(slice_))
                cheb = chebyshev_array(*chebyshev_list)
                res = f(numbers, cheb, ctypes.c_int(N), ctypes.c_int(currM))
                indeces = []
                for i in range(N):
                    indeces.append(res[i])
                    #indeces.append(numbers[i])
                indeces = np.array(indeces)
                if cutoff:
                    cutoff = False
                    indeces = indeces[:measures-batch_i]
                reconstructed[lead+1].extend(indeces)
        clh_client.insert(
            table=table,
            data=reconstructed,
            column_oriented=True,
            settings={'async_insert': True}
        )
        res = clh_client.query(f"""DELETE FROM `{buffer}` WHERE timestamp >= '{start_time}' AND timestamp <= '{end_time}'""")
        clh_client.close()
        return Response(status_code=200)
    except Exception:
        logger.error(traceback.format_exception(*sys.exc_info()))
        clh_client.close()
    return Response(status_code=500)

@app.post("/decompress")
def decompress(user: User, start_time: str, end_time: str, background: BackgroundTasks):
    try:
        table = CH_TABLENAME_FORMAT.format(
            user_id=user.user_id,
            mac=user.mac,
            freq=user.freq
        )
        clh_client = clickhouse.get_client(
            host=CH_HOST,
            user=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE,
            client_name=CH_USER,
        )
        res = clh_client.query(f"""SELECT * FROM `{table}` WHERE timestamp >= '{start_time}' AND timestamp <= '{end_time}' ORDER BY timestamp""")
        record = np.array(res.result_columns)
        measures = len(record[1, :])
        reconstructed = []
        cutoff = False
        reconstructed.append(record[0, :].tolist())
        for lead in range(CHANNEL_NUM):
            reconstructed.append([])
            for batch_i in range(0, measures, N):
                slice_ = record[lead+1, batch_i:batch_i+N].copy()
                if batch_i + N > measures:
                    cutoff = True
                    slice_ = np.append(slice_, [0] * (batch_i + N - measures))
                res = list(slice_ @ chebyshev_matrix)
                #res = list(slice_)
                indeces = []
                indeces.extend(res)
                #indeces = np.array(indeces)
                if cutoff:
                    cutoff = False
                    indeces = indeces[:measures-batch_i]
                reconstructed[lead+1].extend(indeces)
        path = f"response_{datetime.now().strftime("%Y%m%d%H%M%S.%f")}.csv"
        df = pd.DataFrame({"timestamp": reconstructed[0], "first_lead": reconstructed[1], "second_lead": reconstructed[2]})
        df.to_csv(path)
        background.add_task(clear_file, path)
        return FileResponse(path=path)
    except Exception:
        logger.error(traceback.format_exception(*sys.exc_info()))
        clh_client.close()
    return Response(status_code=500)