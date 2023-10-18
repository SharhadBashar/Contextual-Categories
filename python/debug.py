import os
import sys
import json
from pprint import pprint

from constants import *
from predict_iab import Predict_IAB
from predict_apple import Predict_Apple
from att import Audio_To_Text_EN, Audio_To_Text_FR
from helper import download, get_apple_cat, get_iab_cat, load_topics, del_files


def read_inputs_cmd():
    podcast_input = {}
    return podcast_input

def read_inputs_file(language, file_name):
    with open(os.path.join(PATH_DEBUG, file_name)) as file:
        podcast_input = json.load(file)
    return podcast_input[language]

def debug_get_query(data):
    data['PodcastName'] = json.dumps(data['PodcastName']).replace("'", "''").strip('\"')
    data['EpisodeName'] = json.dumps(data['EpisodeName']).replace("'", "''").strip('\"')
    data['Description'] = json.dumps(data['Description']).replace("'", "''").strip('\"')

    return f'''
    Copy the following
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    topics = json.dumps({data['Topics']})
    topics_match = json.dumps({data['TopicsMatch']})
    
    conn = pyodbc.connect(self.conn_dmp)
    query = """UPDATE dbo.ContextualCategories
                SET AppleContentFormatId = {{}},
                    IabV2ContentFormatId = {{}},
                    TransLink = '{{}}',
                    Topics = '{{}}',
                    TopicsMatch = '{{}}',
                    UpdatedDate = '{{}}',
                    Active = 'True',
                    Lock = -1
                WHERE Id = {{}} AND 
                    ShowId = '{{}}' AND 
                    EpisodeId = '{{}}' AND 
                    PublisherId = '{{}}'
            """.format(
                '{data['AppleContentFormatId']}',
                '{data['IabV2ContentFormatId']}',
                '{data['TransLink']}',
                str('{data['Topics']}'),
                str('{data['TopicsMatch']}'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # UpdatedDate
                '{data['Id']}',
                '{data['ShowId']}', 
                '{data['EpisodeId']}', 
                '{data['PublisherId']}'
            )
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    
    <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
'''

def runner(podcast):
    if (podcast['language'] == 'english'):
        att = Audio_To_Text_EN()
    elif (podcast['language'] == 'french'):
        att = Audio_To_Text_FR()
    if (podcast['apple_cat'] != 0):
        predict_apple = Predict_Apple()
        data = podcast['podcast_name'] + podcast['episode_name'] + podcast['description'] + ' '.join(podcast['keywords'])
        apple_cat_cleaned_data = predict_apple.clean_data(data, 'debug', 'debug', podcast['language'])
        apple_cat = predict_apple.predict(apple_cat_cleaned_data, 'debug', 'debug', podcast['language'])
        apple_cat_db = get_apple_cat(apple_cat, 'debug', 'debug', podcast['language'])
    else:
        apple_cat = podcast['apple_cat']
        apple_cat_db = apple_cat
    file_name = download(podcast['episode_id'], podcast['content_url'], 'debug', podcast['language'])
    text = att.transcribe(file_name, 'debug', 'debug', podcast['language'])
    text_file = att.save_text(text, file_name.split('.')[0] + PKL, 'debug', 'debug', podcast['language'])
    Predict_IAB(text_file, 'debug', 'debug', podcast['language'])
    
    db_data = {}
    db_data['Id'] = podcast['id']
    db_data['ShowId'] = podcast['show_id']
    db_data['EpisodeId'] = podcast['episode_id'] 
    db_data['PublisherId'] = podcast['publisher_id']
    db_data['AppleContentFormatId'] = apple_cat_db
    db_data['IabV2ContentFormatId'] = get_iab_cat(text_file, 'debug', 'debug', podcast['language'])
    db_data['PodcastName'] = podcast['podcast_name']
    db_data['EpisodeName'] = podcast['episode_name']
    db_data['Keywords'] = podcast['keywords']
    db_data['ContentType'] = podcast['content_type']
    db_data['ContentUrl'] = podcast['content_url']
    db_data['TransLink'] = 'www.dummy_S3_link.com'
    topics, topics_match = load_topics(text_file, 'debug', 'debug', podcast['language'])
    db_data['Topics'] = topics
    db_data['TopicsMatch'] = topics_match
    db_data['Description'] = podcast['description']
    
    print(debug_get_query(db_data))
    
    del_files(file_name, text_file, 'debug', 'debug', podcast['language'])
    
if __name__ == '__main__':
    try:
        command = sys.argv[1].lower()
    except IndexError:
        print('Type -cmd or -f for command line inputs or json file inputs')
        quit()
    
    if (command == '-f'):
        try:
            language = sys.argv[2].lower()
            file_name = sys.argv[3].lower()
        except:
            file_name = 'input.json'
        podcast_input = read_inputs_file(language, file_name)
    elif (command == '-cmd'):
        podcast_input = read_inputs_cmd()
    else:
        print('Type -cmd or -f for command line inputs or json file inputs')
        quit()
    runner(podcast_input)

