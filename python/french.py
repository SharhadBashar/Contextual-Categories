import os
import time

from s3 import S3
from constants import *
from logger import Logger
from database import Database
from predict_iab import Predict_IAB
from predict_apple import Predict_Apple
from att import Audio_To_Text_FR
from helper import download, get_apple_cat, get_iab_cat, load_topics, del_files, json_response_message

if __name__ == '__main__':
    language = 'french'
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
        att = Audio_To_Text_FR()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Audio To Text: French', error))

    while True:
        podcast = db.get_podcast_new(RADIO_FRANCE_ID)
        if podcast:
            db.update_podcast_lock(podcast['id'])
            Logger(200, LOG_TYPE['i'], PODCAST_REQUEST.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
    
            if (db.get_podcast_count(podcast['publisher_id'], podcast['show_id'], podcast['episode_id']) > 0):
                json_response_message(200, DUPLICATE_PODCAST.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
                db.update_podcast_lock(podcast['id'], lock = -1)
                continue

            if (podcast['podcast_name'] is None or podcast['podcast_name'] == ''):
                json_response_message(404, ERROR_PODCAST_NAME.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
                continue
            if (podcast['episode_name'] is None or podcast['episode_name'] == ''):
                json_response_message(404, ERROR_EPISODE_NAME.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
                continue

            if (podcast['apple_cat'] != 0):
                apple_cat = podcast['apple_cat']
            else:                 
                podcast['description'] = '' if podcast['description'] is None else podcast['description']
                podcast['keywords'] = [] if podcast['keywords'] is None else podcast['keywords']
                data = podcast['podcast_name'] + ' ' + \
                        podcast['episode_name'] + ' ' + \
                        podcast['description'] + ' ' + \
                        ' '.join(podcast['keywords'])
                apple_cat_cleaned_data = predict_apple.clean_data(data, podcast['show_id'], podcast['episode_id'], language)
                apple_cat = predict_apple.predict(apple_cat_cleaned_data, podcast['show_id'], podcast['episode_id'], language)

            file_name = download(podcast['episode_id'], podcast['content_url'], podcast['show_id'], language)

            text = att.transcribe(file_name, podcast['show_id'], podcast['episode_id'], language)
            text_file = att.save_text(text, file_name.split('.')[0] + PKL, podcast['show_id'], podcast['episode_id'], language)

            try:
                s3.upload_file(os.path.join(PATH_DATA_TEXT, text_file), S3_TRANSCRIBE['name'])
                Logger(201, LOG_TYPE['i'], S3_SAVE.format(podcast['episode_id'], os.path.join(S3_URI + S3_TRANSCRIBE['name'], text_file)), podcast['show_id'], podcast['episode_id'], language)
            except Exception as error:
                json_response_message(422, ERROR_S3_SAVE.format(podcast['episode_id'], error), podcast['show_id'], podcast['episode_id'], language)
                continue

            try:
                Predict_IAB(text_file, podcast['episode_id'], podcast['show_id'], language)
            except Exception as error:
                json_response_message(422, ERROR_IAB_PREDICT.format(podcast['episode_id'], error), podcast['show_id'], podcast['episode_id'], language)
                continue

            db_data = {} 
            db_data['Id'] = podcast['id']
            db_data['ShowId'] = podcast['show_id']
            db_data['EpisodeId'] = podcast['episode_id']
            db_data['PublisherId'] = podcast['publisher_id']
            db_data['AppleContentFormatId'] = get_apple_cat(apple_cat, podcast['show_id'], podcast['episode_id'], language)
            db_data['IabV2ContentFormatId'] = get_iab_cat(text_file, podcast['show_id'], podcast['episode_id'], language)
            db_data['TransLink'] = S3_TRANSCRIBE['link'] + text_file
            topics, topics_match = load_topics(text_file, podcast['show_id'], podcast['episode_id'], language)
            db_data['Topics'] = topics
            db_data['TopicsMatch'] = topics_match

            try:
                db.update_podcast(db_data)
                Logger(201, LOG_TYPE['i'], DATA_WRITE.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
            except Exception as error:
                json_response_message(422, ERROR_DB_WRITE.format(podcast['episode_id'], error), podcast['show_id'], podcast['episode_id'], language)
                continue

            del_files(file_name, text_file, podcast['show_id'], podcast['episode_id'], language)

            json_response_message(201, API_SUCCESS.format(podcast['episode_id']), podcast['show_id'], podcast['episode_id'], language)
        else:
            time.sleep(1)
