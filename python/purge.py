import os
from glob import glob
from tqdm import tqdm

from constants import *

def delete():
    audio_files = glob(PATH_DATA_AUDIO + '*')
    category_files = glob(PATH_DATA_CATEGORY + '*')
    text_files = glob(PATH_DATA_TEXT + '*')
    files = audio_files + category_files + text_files
    
    for file in tqdm(files):
        os.remove(file)

if __name__ == '__main__':
    delete()
