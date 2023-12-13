import os
from glob import glob
from tqdm import tqdm

from logger import Logger

from constants import *

def delete():
    audio_files = glob(PATH_DATA_AUDIO + '*')
    category_files = glob(PATH_DATA_CATEGORY + '*')
    text_files = glob(PATH_DATA_TEXT + '*')
    custom_category_files = glob(PATH_CUSTOM_TOPICS + '*')
    files = audio_files + category_files + text_files
    Logger(200, LOG_TYPE['i'], FILE_PRUGE_COUNT.format(len(files)))
    for file in tqdm(files):
        os.remove(file)

if __name__ == '__main__':
    delete()
