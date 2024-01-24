import os
import re
import json
import pickle
from cleantext import clean
import dateutil.parser as parser 
from datetime import datetime, date

from s3 import S3
from constants import *
from logger import Logger
from database import Database

class Custom_Topic:
    def __init__(self, custom_topic, keyword_score_list, total_score = CUSTOM_TOPIC_TOTAL_SCORE, start_date = None, end_date = None):
        self.custom_topic = {
            'custom_topic': custom_topic.lower(),
            'keyword_score': self.get_keyword_score(keyword_score_list),
            'total_score': total_score,
            'start_date': parser.parse(start_date, dayfirst = True).date() if start_date else date.today(),
            'end_date': parser.parse(end_date, dayfirst = True).date() if end_date else start_date.replace(start_date.year + 1)
        }

    def __getitem__(self, key):
        return self.custom_topic[key]
        
    def get_keyword_score(self, keyword_score_list: list) -> list:
        keyword_score = []
        keyword_score_list_len = len(keyword_score_list)
        if (keyword_score_list_len % 2 != 0):
            print('Missing score for a keyword')
            quit()
        for i in range(0, keyword_score_list_len, 2):
            if ('(' in keyword_score_list[i]):
                with_stop_word = keyword_score_list[i].replace('(', '')
                with_stop_word = with_stop_word.replace(')', '')
                keyword_score.append((with_stop_word.lower(), keyword_score_list[i + 1]))
                without_stop_word = re.sub(r'\(.*\)', '', keyword_score_list[i]).replace('  ', ' ').strip()
                keyword_score.append((without_stop_word.lower(), keyword_score_list[i + 1]))
            else:
                keyword_score.append((keyword_score_list[i].lower(), keyword_score_list[i + 1]))
        return keyword_score

class Custom_Topics:
    def __init__(self, text_data_path = None):
        self.text_data_path = text_data_path if text_data_path else PATH_DATA_TEXT
        self.db = Database(env = 'prd')

    def _download_custom_topic_json(self, custom_topic_json):
        S3().download_file(custom_topic_json, S3_CUSTOM_TOPICS['name'], PATH_CUSTOM_TOPICS)

    def _load_custom_topic_json(self, custom_topic_json):
        custom_topic = json.load(open(os.path.join(PATH_CUSTOM_TOPICS, custom_topic_json)))
        if ('total_score' in custom_topic): total_score = custom_topic['total_score'] 
        else: total_score = CUSTOM_TOPIC_TOTAL_SCORE
        if ('start_date' in custom_topic): start_date = custom_topic['start_date'] 
        else: start_date = None
        if ('end_date' in custom_topic): end_date = custom_topic['end_date'] 
        else: end_date = None
        return Custom_Topic(custom_topic['custom_topic'], 
                            custom_topic['keywords'], 
                            total_score, start_date, end_date)

    def _add_custom_topic_db(self, custom_topic: Custom_Topic):
        values = []
        last_custom_id = self.db.write_custom_topic(custom_topic)
        for keyword_score in custom_topic['keyword_score']:
            values.append((*keyword_score, last_custom_id, 
                           datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                           datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
        self.db.write_custom_topic_keyword(values)

    def _delete_custom_topic_json(self, custom_topic_json):
        try:
            os.remove(os.path.join(PATH_CUSTOM_TOPICS, custom_topic_json))
        except Exception as error:
            Logger(422, LOG_TYPE['e'], ERROR_CUSTOM_TOPIC_JSON_DELETE_FILE.format(custom_topic_json, error))

    def add_new_custom_topic(self, custom_topic_json):
        self._download_custom_topic_json(custom_topic_json)
        custom_topic = self._load_custom_topic_json(custom_topic_json)
        self._add_custom_topic_db(custom_topic)
        self._delete_custom_topic_json(custom_topic_json)

    def clean_text(self, text_dict):
        text = text_dict['text']
        text = clean(text, clean_all = False,
						   extra_spaces = True,
						   stemming = False,
						   stopwords = False,
						   lowercase = True,
						   numbers = False,
						   punct = True
					)
        return text

    def find_custom_topic(self, keywords, total_score, text_file):
        podcast_score = 0
        keyword_match = {}
        text = self.clean_text(pickle.load(open(os.path.join(self.text_data_path, text_file), 'rb')))
        for keyword, score in keywords:
            count = text.count(keyword)
            keyword_match[keyword] = count
            podcast_score += score * count
        return podcast_score >= total_score, podcast_score, keyword_match

if __name__ == '__main__':
    Custom_Topics().add_new_custom_topic('euro.json')
