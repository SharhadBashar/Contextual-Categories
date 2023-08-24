from constants import *
from logger import Logger
from database import Database

if __name__ == '__main__':
    try:
        db = Database(env = 'prd')
    except Exception as error:
        print(error)
        Logger(400, LOG_TYPE['e'], ERROR_START_UP.format('Data Base', error))
        
    podcasts = db.get_podcast_fail()
    
    for podcast in podcasts:
        db.update_podcast_lock(podcast['id'], lock = 0)
        language = 'english' if podcast['publisher_id'] == SPREAKER_ID else 'french'
        Logger(201, LOG_TYPE['i'], FAIL_PODCAST_UNLOCK.format(podcast['id']), podcast['show_id'], podcast['episode_id'], language)
