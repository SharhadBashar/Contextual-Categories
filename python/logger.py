import os
import json
import logging
import datetime

from constants import *

'''
Log format:
{
    'timestamp': '',
    'status_code': '',
    'log_type': '',
    'show_id': '',
    'episode_id': '',
    'language': '',
    'message': ''
}
'''
class Logger:
    def __init__(self, status_code, log_type, message, show_id = '', episode_id = '', language = ''):
        logging.basicConfig(filename = os.path.join(PATH_LOG, LOG_FILENAME), 
                                 format = '%(message)s', 
                                 filemode = 'a',
                                 level = logging.ERROR) 
        
        logger = logging.getLogger()
        log = LOG_FORMAT.copy()
        log['timestamp'] = str(datetime.datetime.now())
        log['status_code'] = status_code
        log['log_type'] = log_type
        log['show_id'] = show_id
        log['episode_id'] = episode_id
        log['language'] = language
        log['message'] = message
        logger.error(json.dumps(log))

if __name__ == '__main__':
    Logger(201, LOG_TYPE['i'], API_SUCCESS.format(564645), 1232, 564645, 'english')
    Logger(200, LOG_TYPE['i'], API_RUNNING)
    Logger(422, LOG_TYPE['i'], ERROR_DB_WRITE.format(564645), 1232, 564645, 'french')