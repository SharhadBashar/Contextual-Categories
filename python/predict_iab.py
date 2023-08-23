import os
import torch
import pickle
from tqdm import tqdm
from cleantext import clean
from collections import Counter
from googletrans import Translator

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.stem import WordNetLemmatizer
from sentence_transformers import SentenceTransformer, util

from constants import *
from logger import Logger

class Predict_IAB:
	def __init__(self, text_file, episode_id, show_id,
	      language = 'english',
	      ryan_category = None, 
		  static_data_path = None, 
		  text_data_path = None, 
		  category_path = None,
		  model_name = None):
		self.language = language
		self.static_data_path = static_data_path if static_data_path else PATH_DATA_STATIC_CATEGORY
		self.text_data_path = text_data_path if text_data_path else PATH_DATA_TEXT
		self.category_path = category_path if category_path else PATH_DATA_CATEGORY
		self.ryan_category = ryan_category if ryan_category else RYAN_CAT
		self.model_name = model_name if model_name else IAB_MODELS[1]

		category_list = pickle.load(open(os.path.join(self.static_data_path, self.ryan_category), 'rb'))
		self.get_custom_stopwords()
		text = self.clean_text(pickle.load(open(os.path.join(self.text_data_path, text_file), 'rb')))

		recurring_n_words = self.get_recurring_n(text, n = RECURRING_N)
		if (self.language != 'english'):
			recurring_n_words = self.translate_words(recurring_n_words)
		mapping = self.score_mapping(recurring_n_words, category_list, self.model_name)
		self.save_mapping(mapping, text_file, self.category_path, episode_id, show_id, self.language)

	def get_custom_stopwords(self):
		with open(os.path.join(PATH_STOP_WORDS, 'stop_words_{}.pkl'.format(self.language)), 'rb') as file:
			self.custom_stopwords = pickle.load(file)
		file.close()

	def clean_text(self, text_dict):
		stop = stopwords.words(self.language)
		lemmatizer = WordNetLemmatizer()
		text = text_dict['text'].replace('[^A-Za-z0-9 ]+', ' ')
		text = clean(text, clean_all = False, 
						   extra_spaces = True, 
						   stemming = False,
						   stopwords = True, 
						   lowercase = True, 
						   numbers = True, 
						   punct = True
					)
		text = ' '.join([word for word in text.split() if word not in (stop)])
		text = ' '.join([word for word in text.split() if word not in (self.custom_stopwords)])
		text = ' '.join([lemmatizer.lemmatize(word) for word in text.split()])
		return text

	def get_recurring_n(self, text, n = RECURRING_N):
		return Counter(text.split()).most_common(n)

	def translate_words(self, recurring_n_words):
		translator = Translator()
		for i in range(RECURRING_N):
			translation = translator.translate(recurring_n_words[i][0], src = self.language, dest = 'english').text
			recurring_n_words[i] = (translation.lower(), recurring_n_words[i][1])
		return recurring_n_words

	def score_mapping(self, recurring_n_words, category_list, model_name):
		mapping = dict()
		model = SentenceTransformer(model_name)
		embs_word = torch.zeros(len(recurring_n_words), IAB_MODELS_PRAMS[model_name])
		embs_category = torch.zeros(len(category_list), IAB_MODELS_PRAMS[model_name])

		for i, word in enumerate(tqdm(recurring_n_words)):
			word = word[0].lower()
			embedding_word = model.encode(word, convert_to_tensor = True)
			embs_word[i] = embedding_word

		if (os.path.isfile(os.path.join(self.static_data_path, IAB_CAT_EMB))):
			embs_category = torch.load(os.path.join(self.static_data_path, IAB_CAT_EMB))
		else:
			for i, category in enumerate(tqdm(category_list)):
				category = category[1].lower()
				embedding_category = model.encode(category, convert_to_tensor = True)
				embs_category[i] = embedding_category
			with open(os.path.join(self.static_data_path, IAB_CAT_EMB), 'wb') as file: 
				torch.save(embs_category, file)

		scores, indices = torch.max(util.cos_sim(embs_word, embs_category), dim = -1)

		for i, idx in enumerate(indices):
			mapping[recurring_n_words[i][0]] = {
				'id': category_list[idx][0],
	 		    'data': recurring_n_words[i][0],
	 		    'table': category_list[idx][1],
	 		    'score': round(scores[i].item(), 4),
	 		    'count': recurring_n_words[i][1]
			}
		return mapping

	def save_mapping(self, mapping, mapping_file, category_path, episode_id, show_id, language):
		with open(os.path.join(category_path, mapping_file), 'wb') as file: 
			pickle.dump(mapping, file)
		Logger(200, LOG_TYPE['i'], CAT_SAVE.format(episode_id, os.path.join(category_path, mapping_file)), show_id, episode_id, language)
