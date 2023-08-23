import os
import json
import time
import psutil
import GPUtil
from typing import Union
from collections import deque
from pydantic import BaseModel
from fastapi import FastAPI, status

from s3 import S3
from constants import *
from logger import Logger
from database import Database
from predict_iab import Predict_IAB
from predict_apple import Predict_Apple
from att import Audio_To_Text_EN, Audio_To_Text_FR
from helper import download, get_apple_cat, get_iab_cat, load_topics, sort_hourly_transaction, del_files, json_response_message

class Podcast(BaseModel):
    show_id: str
    episode_id: str
    publisher_id: int
    podcast_name: str
    episode_name: str
    apple_cat: Union[str, None] = None
    content_type: Union[str, None] = None
    description: Union[str, None] = None 
    keywords: Union[list, None] = None 
    content_url: str

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

@app.post('/categorize/english', status_code = status.HTTP_201_CREATED)
def categorize_podcast(podcast: Podcast):
    language = 'english'
    Logger(200, LOG_TYPE['i'], PODCAST_REQUEST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    
    if (db.get_podcast(podcast.publisher_id, podcast.show_id, podcast.episode_id) > 0):
        return json_response_message(200, DUPLICATE_PODCAST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    
    try:
        att_en = Audio_To_Text_EN()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Audio To Text: English', error))

    if (podcast.podcast_name is None or podcast.podcast_name == ''):
        return json_response_message(404, ERROR_PODCAST_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    if (podcast.episode_name is None or podcast.episode_name == ''):
        return json_response_message(404, ERROR_EPISODE_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

    if (podcast.apple_cat and len(podcast.apple_cat) > 0):
        apple_cat = podcast.apple_cat
    else:                 
        podcast.description = '' if podcast.description is None else podcast.description
        podcast.keywords = [] if podcast.keywords is None else podcast.keywords
        data = podcast.podcast_name + ' ' + \
                podcast.episode_name + ' ' + \
                podcast.description + ' ' + \
                ' '.join(podcast.keywords)
        apple_cat_cleaned_data = predict_apple.clean_data(data, podcast.show_id, podcast.episode_id, language)
        apple_cat = predict_apple.predict(apple_cat_cleaned_data, podcast.show_id, podcast.episode_id, language)

    file_name = download(podcast.episode_id, podcast.content_url, podcast.show_id, language)

    text = att_en.transcribe(file_name, podcast.show_id, podcast.episode_id, language)
    text_file = att_en.save_text(text, file_name.split('.')[0] + PKL, podcast.show_id, podcast.episode_id, language)

    try:
        s3.upload_file(os.path.join(PATH_DATA_TEXT, text_file), S3_TRANSCRIBE['name'])
        Logger(201, LOG_TYPE['i'], S3_SAVE.format(podcast.episode_id, os.path.join(S3_URI + S3_TRANSCRIBE['name'], text_file)), podcast.show_id, podcast.episode_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_S3_SAVE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

    try:
        Predict_IAB(text_file, podcast.episode_id, podcast.show_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_IAB_PREDICT.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

    db_data = {} 
    db_data['ShowId'] = podcast.show_id
    db_data['EpisodeId'] = podcast.episode_id 
    db_data['PublisherId'] = podcast.publisher_id
    db_data['AppleContentFormatId'] = get_apple_cat(apple_cat, podcast.show_id, podcast.episode_id, language)
    db_data['IabV2ContentFormatId'] = get_iab_cat(text_file, podcast.show_id, podcast.episode_id, language)
    db_data['PodcastName'] = podcast.podcast_name
    db_data['EpisodeName'] = podcast.episode_name
    db_data['Keywords'] = podcast.keywords if podcast.keywords else []
    db_data['ContentType'] = podcast.content_type if podcast.content_type else 'audio'
    db_data['ContentUrl'] = podcast.content_url
    db_data['TransLink'] = S3_TRANSCRIBE['link'] + text_file
    topics, topics_match = load_topics(text_file, podcast.show_id, podcast.episode_id, language)
    db_data['Topics'] = topics
    db_data['TopicsMatch'] = topics_match
    db_data['Description'] = podcast.description if podcast.description else ''

    try:
        db.write_podcast(db_data)
        Logger(201, LOG_TYPE['i'], DATA_WRITE.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_DB_WRITE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

    del_files(file_name, text_file, podcast.show_id, podcast.episode_id, language)

    return json_response_message(201, API_SUCCESS.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

# @app.post('/categorize/french', status_code = status.HTTP_201_CREATED)
# def categorize_podcast(podcast: Podcast):
#     language = 'french'
#     Logger(200, LOG_TYPE['i'], PODCAST_REQUEST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    
#     if (db.get_podcast(podcast.publisher_id, podcast.show_id, podcast.episode_id) > 0):
#         return json_response_message(200, DUPLICATE_PODCAST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    
#     try:
#         att_fr = Audio_To_Text_FR()
#     except Exception as error:
#         Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Audio To Text: French', error))

#     if (podcast.podcast_name is None or podcast.podcast_name == ''):
#         return json_response_message(404, ERROR_PODCAST_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
#     if (podcast.episode_name is None or podcast.episode_name == ''):
#         return json_response_message(404, ERROR_EPISODE_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

#     if (podcast.apple_cat and len(podcast.apple_cat) > 0):
#         apple_cat = podcast.apple_cat
#     else:                 
#         podcast.description = '' if podcast.description is None else podcast.description
#         podcast.keywords = [] if podcast.keywords is None else podcast.keywords
#         data = podcast.podcast_name + ' ' + \
#                 podcast.episode_name + ' ' + \
#                 podcast.description + ' ' + \
#                 ' '.join(podcast.keywords)
#         apple_cat_cleaned_data = predict_apple.clean_data(data, podcast.show_id, podcast.episode_id, language)
#         apple_cat = predict_apple.predict(apple_cat_cleaned_data, podcast.show_id, podcast.episode_id, language)

#     file_name = download(podcast.episode_id, podcast.content_url, podcast.show_id, language)

#     text = att_fr.transcribe(file_name, podcast.show_id, podcast.episode_id, language)
#     text_file = att_fr.save_text(text, file_name.split('.')[0] + PKL, podcast.show_id, podcast.episode_id, language)

#     try:
#         s3.upload_file(os.path.join(PATH_DATA_TEXT, text_file), S3_TRANSCRIBE['name'])
#         Logger(201, LOG_TYPE['i'], S3_SAVE.format(podcast.episode_id, os.path.join(S3_URI + S3_TRANSCRIBE['name'], text_file)), podcast.show_id, podcast.episode_id, language)
#     except Exception as error:
#         return json_response_message(422, ERROR_S3_SAVE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

#     try:
#         Predict_IAB(text_file, podcast.episode_id, podcast.show_id, language)
#     except Exception as error:
#         return json_response_message(422, ERROR_IAB_PREDICT.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

#     db_data = {} 
#     db_data['ShowId'] = podcast.show_id
#     db_data['EpisodeId'] = podcast.episode_id 
#     db_data['PublisherId'] = podcast.publisher_id
#     db_data['AppleContentFormatId'] = get_apple_cat(apple_cat, podcast.show_id, podcast.episode_id, language)
#     db_data['IabV2ContentFormatId'] = get_iab_cat(text_file, podcast.show_id, podcast.episode_id, language)
#     db_data['PodcastName'] = podcast.podcast_name
#     db_data['EpisodeName'] = podcast.episode_name
#     db_data['Keywords'] = podcast.keywords if podcast.keywords else []
#     db_data['ContentType'] = podcast.content_type if podcast.content_type else 'audio'
#     db_data['ContentUrl'] = podcast.content_url
#     db_data['TransLink'] = S3_TRANSCRIBE['link'] + text_file
#     topics, topics_match = load_topics(text_file, podcast.show_id, podcast.episode_id, language)
#     db_data['Topics'] = topics
#     db_data['TopicsMatch'] = topics_match
#     db_data['Description'] = podcast.description if podcast.description else ''

#     try:
#        db.write_podcast(db_data)
#        Logger(201, LOG_TYPE['i'], DATA_WRITE.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
#     except Exception as error:
#         return json_response_message(422, ERROR_DB_WRITE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

#     del_files(file_name, text_file, podcast.show_id, podcast.episode_id, language)

#     return json_response_message(201, API_SUCCESS.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

@app.post('/categorize/radiofrench', status_code = status.HTTP_201_CREATED)
def categorize_podcast_apple_temp(podcast: Podcast):
    language = 'french'
    
    if (db.get_podcast(podcast.publisher_id, podcast.show_id, podcast.episode_id) > 0):
        return json_response_message(200, DUPLICATE_PODCAST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    
    if (podcast.podcast_name is None or podcast.podcast_name == ''):
        return json_response_message(404, ERROR_PODCAST_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    if (podcast.episode_name is None or podcast.episode_name == ''):
        return json_response_message(404, ERROR_EPISODE_NAME.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

    podcast.description = '' if podcast.description is None else podcast.description
    podcast.keywords = [] if podcast.keywords is None else podcast.keywords

    db_data = {} 
    db_data['ShowId'] = podcast.show_id
    db_data['EpisodeId'] = podcast.episode_id 
    db_data['PublisherId'] = podcast.publisher_id
    db_data['AppleContentFormatId'] = get_apple_cat(podcast.apple_cat, podcast.show_id, podcast.episode_id, language)
    db_data['IabV2ContentFormatId'] = -1
    db_data['PodcastName'] = podcast.podcast_name
    db_data['EpisodeName'] = podcast.episode_name
    db_data['Keywords'] = podcast.keywords if podcast.keywords else []
    db_data['ContentType'] = podcast.content_type if podcast.content_type else 'audio'
    db_data['ContentUrl'] = podcast.content_url
    db_data['TransLink'] = ''
    db_data['Topics'] = ''
    db_data['TopicsMatch'] = ''
    db_data['Description'] = podcast.description if podcast.description else ''

    db.write_podcast_apple_cat_temp(db_data)

@app.post('/categorize/french', status_code = status.HTTP_201_CREATED)
def categorize_podcast_apple_temp(podcast: Podcast):
    language = 'french'
    Logger(200, LOG_TYPE['i'], PODCAST_REQUEST.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)

    temp_podcast = db.get_podcast_temp(podcast.publisher_id, podcast.show_id, podcast.episode_id)
    while not temp_podcast:
        time.sleep(0.5)
        temp_podcast = db.get_podcast_temp(podcast.publisher_id, podcast.show_id, podcast.episode_id)

    try:
        att_fr = Audio_To_Text_FR()
    except Exception as error:
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Audio To Text: French', error))

    file_name = download(podcast.episode_id, podcast.content_url, podcast.show_id, language)

    text = att_fr.transcribe(file_name, podcast.show_id, podcast.episode_id, language)
    text_file = att_fr.save_text(text, file_name.split('.')[0] + PKL, podcast.show_id, podcast.episode_id, language)

    try:
        s3.upload_file(os.path.join(PATH_DATA_TEXT, text_file), S3_TRANSCRIBE['name'])
        Logger(201, LOG_TYPE['i'], S3_SAVE.format(podcast.episode_id, os.path.join(S3_URI + S3_TRANSCRIBE['name'], text_file)), podcast.show_id, podcast.episode_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_S3_SAVE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

    try:
        Predict_IAB(text_file, podcast.episode_id, podcast.show_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_IAB_PREDICT.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)
    
    db_data = {} 
    db_data['ShowId'] = podcast.show_id
    db_data['EpisodeId'] = podcast.episode_id 
    db_data['PublisherId'] = podcast.publisher_id
    db_data['AppleContentFormatId'] = get_apple_cat(podcast.apple_cat, podcast.show_id, podcast.episode_id, language)
    db_data['IabV2ContentFormatId'] = get_iab_cat(text_file, podcast.show_id, podcast.episode_id, language)
    db_data['PodcastName'] = podcast.podcast_name
    db_data['EpisodeName'] = podcast.episode_name
    db_data['Keywords'] = podcast.keywords if podcast.keywords else []
    db_data['ContentType'] = podcast.content_type if podcast.content_type else 'audio'
    db_data['ContentUrl'] = podcast.content_url
    db_data['TransLink'] = S3_TRANSCRIBE['link'] + text_file
    topics, topics_match = load_topics(text_file, podcast.show_id, podcast.episode_id, language)
    db_data['Topics'] = topics
    db_data['TopicsMatch'] = topics_match
    db_data['Description'] = podcast.description if podcast.description else ''

    try:
       db.update_podcast_temp(db_data)
       Logger(201, LOG_TYPE['i'], DATA_WRITE.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_DB_WRITE.format(podcast.episode_id, error), podcast.show_id, podcast.episode_id, language)

    del_files(file_name, text_file, podcast.show_id, podcast.episode_id, language)

    return json_response_message(201, API_SUCCESS.format(podcast.episode_id), podcast.show_id, podcast.episode_id, language)
