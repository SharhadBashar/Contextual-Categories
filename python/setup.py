import os
import sys
import json
from tqdm import tqdm

from s3 import S3
from constants import *

def runner():
    print('Creating directories...')
    for directory in tqdm(SETUP['directory']):
        if ('log' in directory):
            try:
                os.mkdir('../logs/')
                os.mkdir(directory)
            except:
                None
        else:
            try:
                os.mkdir(directory)
            except:
                None
    print('Directories created')

    f = open(os.path.join(PATH_LOG, LOG_FILENAME), 'w')
    f.write(json.dumps(LOG_SETUP_MESSAGE))
    f.write('\n')
    f.close()

    print('Downloading required files...')
    s3 = S3()
    for file, download_path in tqdm(SETUP['download'].items()):
        s3.download_file(file, S3_CONTEXTUAL_WEB_API['name'], download_path)
    print('Files downloaded')
    print('SETUP COMPLETE')

def create_directory(directory):
    print('Creating directory {}'.format(directory))
    if ('log' in directory):
        try:
            os.mkdir('../logs/')
            os.mkdir(directory)
        except:
            None
        f = open(os.path.join(PATH_LOG, LOG_FILENAME), 'w')
        f.write(json.dumps(LOG_SETUP_MESSAGE))
        f.write('\n')
        f.close()
    elif (directory in SETUP['directory']):
        try:
            os.mkdir(directory)
        except:
            None
    print('Directory created')

def download(file):
    s3 = S3()
    s3.download_file(file, S3_CONTEXTUAL_WEB_API['name'], SETUP['download'][file])
    print('{} downloaded'.format(file))

if __name__ == '__main__':
    try:
        command = sys.argv[1].lower()
    except IndexError:
        runner()
        quit()

    if (command == '-d'):
        file_name = str(sys.argv[2].lower())
        if (file_name not in SETUP['download'].keys()):
            print('File name not found. Please check again')
            quit()
        download(file_name)

    elif (command == '-cd'):
        dir_name = str(sys.argv[2].lower())
        if (dir_name not in SETUP['directory']):
            print('Directory name not found. Please check again')
            quit()
        create_directory(dir_name)

    else:
        print('Command not recognized. Please enter -d for download or nothing to run the entire setup')
