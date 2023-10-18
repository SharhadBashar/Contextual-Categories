import os
import json
import pickle
import requests
from typing import List
from fastapi.responses import JSONResponse

from constants import *
from logger import Logger

def json_response_message(code, message, show_id = '', episode_id = '', language = ''):
    log_type = LOG_TYPE['e'] if 'Error ->' in message else LOG_TYPE['i']
    Logger(code, log_type, message, show_id, episode_id, language)
    return JSONResponse(
            status_code = code,
            content = {log_type: message},
        )

def download(episode_id, url, show_id, language = 'english'):
    try:
        r = requests.get(url, allow_redirects = True)
        r = requests.get(r.url, allow_redirects = True)
        with open(PATH_DATA_AUDIO + episode_id + MP3, 'wb') as file:
            file.write(r.content)
        file.close()
        Logger(201, LOG_TYPE['i'], PODCAST_DOWNLOAD.format(episode_id, PATH_DATA_AUDIO + episode_id + MP3), show_id, episode_id, language)
        return episode_id + MP3
    except Exception as error:
        return json_response_message(404, ERROR_DOWNLOAD.format(episode_id, error), show_id, episode_id, language)
    
def get_apple_cat(apple_cat, show_id, episode_id, language):
    apple_cat = apple_cat.title()
    try:
        file = open(os.path.join(PATH_DATA_STATIC_CATEGORY, APPLE_CAT), 'rb')
        data = dict(pickle.load(file))
        return data[apple_cat]
    except Exception as error:
        return json_response_message(422, ERROR_GET_APPLE_CAT.format(episode_id, error), show_id, episode_id, language)

def get_iab_cat(text_file, show_id, episode_id, language):
    try:
        iab_cat = -1 
        highest_score = 0
        file = open(os.path.join(PATH_DATA_CATEGORY, text_file), 'rb')
        data = dict(pickle.load(file))
        for key, val in data.items():
            if (val['score'] < 0.5):
                continue
            score = val['score'] * val['count']
            if (score > highest_score):
                iab_cat = val['id']
                highest_score = score
        return iab_cat
    except Exception as error:
        return json_response_message(422, ERROR_GET_IAB_CAT.format(episode_id, error), show_id, episode_id, language)

def load_topics(text_file, show_id, episode_id, language):
    try:
        file = open(os.path.join(PATH_DATA_CATEGORY, text_file), 'rb')
        data = pickle.load(file)
        return json.dumps(list(data.keys()), ensure_ascii = False), json.dumps(data, ensure_ascii = False)
    except Exception as error:
        return json_response_message(422, ERROR_TOPICS.format(episode_id, error), show_id, episode_id, language)

def del_files(file_name, text_file, show_id, episode_id, language):
    try:
        if os.path.isfile(os.path.join(PATH_DATA_AUDIO, file_name)):
            os.remove(os.path.join(PATH_DATA_AUDIO, file_name))
        if os.path.isfile(os.path.join(PATH_DATA_TEXT, text_file)):
            os.remove(os.path.join(PATH_DATA_TEXT, text_file))
        if os.path.isfile(os.path.join(PATH_DATA_CATEGORY, text_file)):
            os.remove(os.path.join(PATH_DATA_CATEGORY, text_file))
        Logger(201, LOG_TYPE['i'], DATA_DELETE.format(episode_id), show_id, episode_id, language)
    except Exception as error:
        return json_response_message(422, ERROR_DELETE_FILES.format(episode_id, error), show_id, episode_id, language)

def sort_hourly_transaction(publisher_count_list):
    if (type(publisher_count_list) != list):
        return 'List {} is not valid.'.format(publisher_count_list)
    if (len(publisher_count_list) == 0):
        return 'List {} is empty.'.format(publisher_count_list)
    total = 0
    message = {}
    message['Title'] = 'In the past hour'
    for publisher in publisher_count_list:
        message['Publisher {}'.format(publisher[0])] = '{} podcasts categorized'.format(publisher[1])
        total += publisher[1]
    message['Total'] = '{} podcasts categorized'.format(total)
    return message
