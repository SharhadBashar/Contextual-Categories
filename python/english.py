import os
import json
import time

from s3 import S3
from constants import *
from logger import Logger
from database import Database
from predict_iab import Predict_IAB
from predict_apple import Predict_Apple
from att import Audio_To_Text_EN, Audio_To_Text_FR
from helper import download, get_apple_cat, get_iab_cat, load_topics, sort_hourly_transaction, del_files, json_response_message

if __name__ == '__main__':
    try:
        s3 = S3()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('AWS S3', error))

    try:
        db = Database(env = 'prd')
    except Exception as error:
        print(error)
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Data Base', error))

    try:
        predict_apple = Predict_Apple()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Predicting Apple Categories', error))

    try:
        att_en = Audio_To_Text_EN()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Audio To Text: English', error))

    while True:
        podcast = db.get_podcast_new(SPREAKER_ID)
        if podcast:
            None
        else:
            time.sleep(1)
