import os
import pickle
from cleantext import clean

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.stem import WordNetLemmatizer

from constants import *
from helper import json_response_message

class Predict_Apple:
    def __init__(self, apple_cat_map = None, model_filename = None, static_cat_path = None, model_path = None):
        self.apple_cat_map = apple_cat_map if apple_cat_map else APPLE_CAT_MAP_EN
        self.static_cat_path = static_cat_path if static_cat_path else PATH_DATA_STATIC_CATEGORY
        self.model_path = model_path if model_path else PATH_MODEL
        self.model_filename = model_filename if model_filename else MODEL

        self.category_dict = pickle.load(open(os.path.join(self.static_cat_path, self.apple_cat_map), 'rb'))
        self.model = pickle.load(open(os.path.join(self.model_path, self.model_filename), 'rb'))
        
    def clean_data(self, data, show_id, episode_id, language = 'english'):
        lemmatizer = WordNetLemmatizer()
        data = data.replace('[^A-Za-z0-9 ]+', ' ')
        data = clean(data, clean_all = False, 
                           extra_spaces = True, 
                           stemming = False,
                           stopwords = True, 
                           lowercase = True, 
                           numbers = True, 
                           punct = True
                    )
        data = ' '.join([lemmatizer.lemmatize(word) for word in data.split()])
        if (data is None):
            return json_response_message(422, ERROR_CLEAN_DATA.format(episode_id), show_id, episode_id, language)
        return data
    
    def predict(self, inp, show_id, episode_id, language = 'english'):
        try:
            return self.category_dict[self.model.predict([inp])[0]]
        except Exception as error:
            return json_response_message(422, ERROR_PREDICT.format(episode_id, error), show_id, episode_id, language)
