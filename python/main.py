import os
import json
import time
import psutil
import GPUtil
from collections import deque
from fastapi import FastAPI, status

from s3 import S3
from constants import *
from purge import delete
from logger import Logger
from database import Database
from check_file_update import update
from custom_topics import Custom_Topics
from helper import sort_hourly_transaction, json_response_message, add_stop_word

try:
    db = Database(env = 'prd')
except Exception as error:
    print(error)
    Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Data Base', error))

app = FastAPI()

@app.get('/status', status_code = status.HTTP_200_OK)
def status_check():
    return json_response_message(200, API_RUNNING)

@app.get('/welcome', status_code = status.HTTP_200_OK)
def intro():
    return WELCOME

@app.get('/transaction', status_code = status.HTTP_200_OK)
def get_hourly_transaction():
    return sort_hourly_transaction(db.get_hourly_transaction())
    
@app.get('/cpu', status_code = status.HTTP_200_OK)
def get_cpu_useage():
    Logger(200, LOG_TYPE['i'], CPU_USEAGE.format(os.cpu_count(), *psutil.getloadavg()))
    Logger(200, LOG_TYPE['i'], CPU_MEM_USEAGE.format(round(psutil.virtual_memory()[0]/1000000000, 2), 
                                                    round(psutil.virtual_memory()[1]/1000000000, 2),
                                                    round(psutil.virtual_memory()[3]/1000000000, 2),
                                                    round(psutil.virtual_memory()[2]/1000000000, 2)))

@app.get('/gpu', status_code = status.HTTP_200_OK)
def get_gpu_useage():
    GPUs = GPUtil.getGPUs()
    if (len(GPUs) > 0):
        id, load, memory_util = GPUs[0].id, round(GPUs[0].load * 100, 2), round(GPUs[0].memoryUtil * 100, 2)
    else:
        id, load, memory_util = 'NaN', 0, 0
    Logger(200, LOG_TYPE['i'], GPU_USEAGE.format(id, load, memory_util))
    
@app.get('/log', status_code = status.HTTP_200_OK)
def get_log():
    json_list = []
    with open(os.path.join(PATH_LOG, LOG_FILENAME)) as file:
        for json_obj in file:
            if (json_obj is not None):
                json_list.append(json.loads(json_obj))
    json_list = json_list[::-1]
    title = json_list.pop()
    json_list = deque(json_list)
    json_list.appendleft(title)
    return json_list

@app.get('/update/{file_name}', status_code = status.HTTP_200_OK)
def update_file(file_name):
    if (file_name in list(SETUP['download'].keys())):
        update(file_name, S3())
        if (time.time() - os.stat(os.path.join(SETUP['download'][file_name], file_name))[8] < FILE_UPDATE_TIME_DELTA):
            Logger(200, LOG_TYPE['i'], FILE_UPDATE.format(file_name), language = file_name.split('_')[2].split('.')[0])
        else:
            Logger(422, LOG_TYPE['e'], FILE_UPDATE_FAIL.format(file_name), language = file_name.split('_')[2].split('.')[0])
    else:
        Logger(404, LOG_TYPE['e'], FILE_UPDATE_WRONG_FILE.format(file_name), language = file_name.split('_')[2].split('.')[0])

@app.get('/add_stop_word/{language}/{stop_word}', status_code = status.HTTP_200_OK)
def add(language, stop_word):
    stop_word = stop_word.lower()
    result = add_stop_word(stop_word, language)
    if result:
        Logger(201, LOG_TYPE['i'], STOP_WORD_ADDED.format(stop_word, language))
    else:
        Logger(422, LOG_TYPE['e'], STOP_WORD_ADDED_FAILED.format(stop_word, language))
    S3().upload_file(os.path.join(PATH_STOP_WORDS, 'stop_words_{}.pkl'.format(language)), S3_CONTEXTUAL_WEB_API['name'])
    Logger(200, LOG_TYPE['i'], STOP_WORD_FILE_UPLOADED.format(language))

@app.get('/add_custom_topic/{custom_topic_json}', status_code = status.HTTP_200_OK)
def add_custom_topic(custom_topic_json):
    try:
        Custom_Topics().add_new_custom_topic(custom_topic_json)
        Logger(200, LOG_TYPE['i'], NEW_CUSTOM_TOPIC_ADDED.format(custom_topic_json))
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_NEW_CUSTOM_TOPIC_ADDED.format(custom_topic_json, error))
    

@app.get('/pur9e', status_code = status.HTTP_200_OK)
def purge():
    delete()
