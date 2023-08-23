import os

from s3 import S3
from constants import *
from logger import Logger

def update(file, s3):
    s3.download_file(file, S3_CONTEXTUAL_WEB_API['name'], SETUP['download'][file])
    print('{} updated'.format(file))

def check(s3):
    for file_name, file_path in SETUP['download'].items():
        obj = s3.get_info(S3_CONTEXTUAL_WEB_API['name'], file_name)
        if (int(obj.last_modified.strftime('%s')) != int(os.path.getmtime(os.path.join(file_path, file_name)))):
            try:
                update(file_name, s3)
                Logger(200, LOG_TYPE['i'], FILE_UPDATE.format(file_name))
            except Exception as error:
                Logger(422, LOG_TYPE['e'], FILE_UPDATE_FAIL.format(file_name))

if __name__ == '__main__':
    check(S3())