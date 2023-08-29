import os
import json
import pyodbc
from datetime import datetime, timedelta

from constants import *

class Database:
    def __init__(self, env = 'prod'):
        with open(os.path.join(PATH_CONFIG, DB_CONFIG)) as file:
            database_info = json.load(file)
        self.conn_common = self._database_conn(database_info[env], 'common')
        self.conn_dmp = self._database_conn(database_info[env], 'dmp')
        
    def _database_conn(self, database_info, database):
        return 'DRIVER={};\
                    SERVER={};\
                    DATABASE={};\
                    UID={};\
                    PWD={};\
                    TrustServerCertificate=yes'.format(
            database_info['driver'], database_info['server'], 
            database_info['database'][database],
            database_info['username'], database_info['password']
        )

    def get_podcast_count(self, publisher_id, show_id, episode_id):
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT COUNT(Id)
                   FROM dbo.ContextualCategories
                   WHERE PublisherId = {} AND ShowId = '{}' AND EpisodeId = '{}'
                """.format(publisher_id, show_id, episode_id)
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()
        return count 

    def get_hourly_transaction(self, time_diff = -1):
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT PublisherId, COUNT(*) AS Total
                   FROM dbo.ContextualCategories
                   WHERE CreatedDate > DATEADD(HOUR, {}, GETDATE())
                   GROUP BY PublisherId
                """.format(time_diff)
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchall()
        cursor.close()
        return count

    def get_podcast_new(self, publisher_id):
        podcast = {}
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT Id, ShowId, EpisodeId, PublisherId, 
                    AppleContentFormatId,
                    PodcastName, EpisodeName, Description, Keywords,
                    ContentUrl
                   FROM dbo.ContextualCategories
                   WHERE PublisherId = {} AND Active = 'False' AND Lock = 0
                   LIMIT 1
                """.format(publisher_id)
        cursor = conn.cursor()
        cursor.execute(query)
        podcast_db = cursor.fetchone()
        cursor.close()
        try:
            podcast['id'] = podcast_db[0]
            podcast['show_id'] = podcast_db[1]
            podcast['episode_id'] = podcast_db[2]
            podcast['publisher_id'] = podcast_db[3]
            podcast['apple_cat'] = podcast_db[4]
            podcast['podcast_name'] = podcast_db[5]
            podcast['episode_name'] = podcast_db[6]
            podcast['description'] = podcast_db[7]
            podcast['keywords'] = podcast_db[8]
            podcast['content_url'] = podcast_db[9]
            return podcast
        except:
            return None

    def get_podcast_fail(self, fail_tolerance = 1):
        podcasts = []
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT Id, ShowId, EpisodeId, PublisherId
                   FROM dbo.ContextualCategories
                   WHERE Lock = 1 AND UpdatedDate > '{}'
                """.format(datetime.now() - timedelta(days = fail_tolerance))
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            podcasts.append({
                'id': row[0],
                'show_id': row[1],
                'episode_id': row[2],
                'publisher_id': row[3]
            })
        cursor.close()
        return podcasts
        
    def write_podcast(self, data):
        data['PodcastName'] = json.dumps(data['PodcastName']).replace("'", "''").strip('\"')
        data['EpisodeName'] = json.dumps(data['EpisodeName']).replace("'", "''").strip('\"')
        data['Description'] = json.dumps(data['Description']).replace("'", "''").strip('\"')

        conn = pyodbc.connect(self.conn_dmp)
        query = """INSERT INTO 
                   dbo.ContextualCategories 
                   (ShowId, EpisodeId, PublisherId, AppleContentFormatId, IabV2ContentFormatId, 
                    Active, CreatedDate, UpdatedDate,
                    PodcastName, EpisodeName, Keywords,
                    ContentType, ContentUrl, TransLink,
                    Topics, TopicsMatch, Description)
                   VALUES 
                    ('{}', '{}', {}, {}, {},
                    'True', '{}', '{}', 
                    '{}', '{}', '{}',
                    '{}', '{}', '{}', 
                    '{}', '{}', '{}')
                """.format( 
                    data['ShowId'], 
                    data['EpisodeId'], 
                    data['PublisherId'], 
                    data['AppleContentFormatId'], 
                    data['IabV2ContentFormatId'], 
                    # data['Active'] -> Always True initially, 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # CreatedDate
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # UpdatedDate
                    data['PodcastName'],
                    data['EpisodeName'],
                    data['Keywords'],
                    data['ContentType'],
                    data['ContentUrl'],
                    data['TransLink'],
                    str(data['Topics']),
                    str(data['TopicsMatch']),
                    data['Description']
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()

    def update_podcast_lock(self, id, lock = 1):
        conn = pyodbc.connect(self.conn_dmp)
        query = """UPDATE dbo.ContextualCategories
                   SET Lock = {}, UpdatedDate = '{}',
                   WHERE Id = {}
                """.format(
                    lock,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    id
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()

    def update_podcast(self, data):
        conn = pyodbc.connect(self.conn_dmp)
        query = """UPDATE dbo.ContextualCategories
                   SET AppleContentFormatId = {},
                        IabV2ContentFormatId = {},
                        TransLink = '{}',
                        Topics = '{}',
                        TopicsMatch = '{}'
                        UpdatedDate = '{}',
                        Active = 'True',
                        Lock = 0
                   WHERE Id = {}, 
                        ShowId = '{}', 
                        EpisodeId = '{}', 
                        PublisherId = '{}'
                """.format(
                    data['AppleContentFormatId'],
                    data['IabV2ContentFormatId'],
                    data['TransLink'],
                    str(data['Topics']),
                    str(data['TopicsMatch']),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # UpdatedDate
                    data['id'],
                    data['ShowId'], 
                    data['EpisodeId'], 
                    data['PublisherId']
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()
