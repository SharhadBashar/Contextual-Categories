import os

GPU_LOAD = 0.98
RECURRING_N = 5
NICE_VAL = 3
SPREAKER_ID = 68
RADIO_FRANCE_ID = 51

# Path
PATH_DATA = '../data/'
PATH_MODEL = '../model/'
PATH_CONFIG = '../config/'
PATH_LOG = '../logs/internal/'
PATH_DEBUG = '../debug/'

PATH_DATA_AUDIO = os.path.join(PATH_DATA, 'audio/')
PATH_DATA_CATEGORY = os.path.join(PATH_DATA, 'category/')
PATH_DATA_STATIC_CATEGORY = os.path.join(PATH_DATA, 'static_category/')
PATH_DATA_TEXT = os.path.join(PATH_DATA, 'text/')
PATH_STOP_WORDS = os.path.join(PATH_DATA, 'stop_words/')

# Files
STOP_WORDS_EN = 'stop_words_english.pkl'
STOP_WORDS_FR = 'stop_words_french.pkl'
APPLE_CAT = 'apple_cat.pkl'
IAB_CAT = 'iab_cat.pkl'
APPLE_CAT_MAP_EN = 'apple_cat_map_en.pkl'
IAB_CAT_EMB = 'iab_cat_embedding.t'
RYAN_CAT = 'ryan_category_id.pkl'
DB_CONFIG = 'database.json'
MODEL = 'model.pkl'
LOG_FILENAME = 'logging.log'

# File formats
MP3 = '.mp3'
WAV = '.wav'
PKL = '.pkl'
TXT = '.txt'
LOG = '.log'
JSON = '.json'
S3_URI = 's3://'

# Models
WHISPER_MODEL_TYPES = ['tiny.en', 'tiny', 'small', 'base', 'medium', 'large']
IAB_MODELS = ['sentence-transformers/all-mpnet-base-v2', 'diptanuc/all-mpnet-base-v2', 'bert-base-nli-mean-tokens', 'bert-large-uncased']
IAB_MODELS_PRAMS = {
    'sentence-transformers/all-mpnet-base-v2': 768, 
    'diptanuc/all-mpnet-base-v2': 768,
    'bert-base-nli-mean-tokens': 768,
    'bert-large-uncased': 1024
}

WELCOME = '''Welcome to Contextual web API.
             Please go to "home_url/categorize/" with the following body to get started:
             show_id: int
             episode_id: int
             publisher_id: int
                 podcast_name: str
                 episode_name: str
                 description: str or ''
                 keywords: list or ''
                 content_url: str
                 Please go to "home_url/docs/" to see all the different API calls and information
                 Please go to "home_url/status/" to see API status
              '''

LOG_SETUP_MESSAGE = {'title': 'Contextual web API log file'}
LOG_TYPE = {'i': 'info', 'e': 'error'}
LOG_FORMAT = {
    'timestamp': '',
    'status_code': '',
    'log_type': '',
    'show_id': '',
    'episode_id': '',
    'language': '',
    'message': ''
}

S3_TRANSCRIBE = {
    'name': 'ts-transcription',
    'link': 'https://s3.console.aws.amazon.com/s3/buckets/ts-transcription?region=us-east-1&prefix='
}
S3_CONTEXTUAL_WEB_API = {
    'name': 'ts-contextual-web-api',
    'link': 'https://s3.console.aws.amazon.com/s3/buckets/ts-contextual-web-api?region=us-east-1'
}
SETUP = {
    'directory': [
        PATH_DATA,
        PATH_MODEL,
        PATH_CONFIG,
        PATH_DATA_AUDIO,
        PATH_DATA_CATEGORY,
        PATH_DATA_STATIC_CATEGORY,
        PATH_DATA_TEXT,
        PATH_LOG,
        PATH_STOP_WORDS
    ],
    'download': {
        STOP_WORDS_EN: PATH_STOP_WORDS,
        STOP_WORDS_FR: PATH_STOP_WORDS,
        DB_CONFIG: PATH_CONFIG,
        APPLE_CAT: PATH_DATA_STATIC_CATEGORY,
        IAB_CAT: PATH_DATA_STATIC_CATEGORY,
        APPLE_CAT_MAP_EN: PATH_DATA_STATIC_CATEGORY,
        IAB_CAT_EMB: PATH_DATA_STATIC_CATEGORY,
        RYAN_CAT: PATH_DATA_STATIC_CATEGORY,
        MODEL: PATH_MODEL
    }
}

# Info Messages:
API_RUNNING = 'API is up and running. WOOHOO!!!'
PODCAST_REQUEST = '[Podcast {}] Recieved request'
API_SUCCESS = '[Podcast {}] Categorized successfully'
PODCAST_DOWNLOAD = '[Podcast {}] Downloaded successfully at {}'
TRANSCRIBE_SAVE = '[Podcast {}] Transcribed successfully at {}'
S3_SAVE = '[Podcast {}] Uploaded successfully to {}'
CAT_SAVE = '[Podcast {}] Category mapping successfully saved at {}'
DATA_WRITE = '[Podcast {}] DB write successful'
DATA_DELETE = '[Podcast {}] Deleted successfully'
FILE_UPDATE = '[File {}] Updated successfully'
DUPLICATE_PODCAST = '[Podcast {}] Already categorized and in Database'
DEVICE_USEAGE = 'Transcribed using {}'
GPU_USEAGE = 'GPU ID: {}, Load: {}%, Memory: {}%'
CPU_USEAGE = 'CPU Cores: {}, CPU Load: 1 min: {}%, 5 min: {}%, 15 min: {}%'
CPU_MEM_USEAGE = 'Total: {} gb, Available: {} gb, Used: {} gb, Percent: {}%'
FAIL_PODCAST_UNLOCK = '[DB ID {}] Failed Podcast unlocked'

# Error Messages
ERROR_START_UP = 'Startup Error with {}. Full Error Traceback: {}'
ERROR_PODCAST_NAME = '[Podcast {}] Error -> Podcast name missing'
ERROR_EPISODE_NAME = '[Podcast {}] Error -> Episode name missing'
ERROR_CLEAN_DATA = '[Podcast {}] Error -> class: predict_apple; function: clean_data'
ERROR_PREDICT = '[Podcast {}] Error -> class: predict_apple; function: predict. Full Error Traceback: {}'
ERROR_DOWNLOAD = '[Podcast {}] Error -> unable to download podcast. Full Error Traceback: {}'
ERROR_WHISPER_MODEL = '[{}] is not a valid model type for whisper'
ERROR_TRANSCRIBE = '[Podcast {}] Error -> class: att; function: transcribe. Full Error Traceback: {}'
ERROR_SAVE_TEXT = '[Podcast {}] Error -> class: att; function: save_text. Full Error Traceback: {}'
ERROR_S3_SAVE = '[Podcast {}] Error -> unable to upload transcribed test to S3 bucket. Full Error Traceback: {}'
ERROR_IAB_PREDICT = '[Podcast {}] Error -> class: predict_iab. Full Error Traceback: {}'
ERROR_GET_APPLE_CAT = '[Podcast {}] Error -> class: helper; function: get_apple_cat. Full Error Traceback: {}'
ERROR_GET_IAB_CAT = '[Podcast {}] Error -> class: helper; function: get_iab_cat. Full Error Traceback: {}'
ERROR_TOPICS = '[Podcast {}] Error -> class: helper; function: load_topics. Full Error Traceback: {}'
ERROR_DELETE_FILES = '[Podcast {}] Error -> class: helper; function: del_files. Full Error Traceback: {}'
ERROR_DB_WRITE = '[Podcast {}] Error -> unable to write to database. Full Error Traceback: {}'
FILE_UPDATE_FAIL = '[File {}] Could NOT be updated'
