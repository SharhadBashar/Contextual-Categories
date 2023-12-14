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
                   WHERE PublisherId = {} AND ShowId = '{}' AND EpisodeId = '{}' AND Active = 'True'
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
                   WHERE UpdatedDate > DATEADD(HOUR, {}, GETDATE()) AND Active = 'True' AND Lock = -1
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
        query = """SELECT TOP(1) Id, ShowId, EpisodeId, PublisherId, 
                    AppleContentFormatId,
                    PodcastName, EpisodeName, Description, Keywords,
                    ContentUrl
                   FROM dbo.ContextualCategories
                   WHERE PublisherId = {} AND Active = 'False' AND Lock = 0
                   ORDER BY Id DESC
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

    def get_podcast_new_custom_topic(self, publisher_id):
        podcast = {}
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT TOP(1) Id, ShowId, EpisodeId, PublisherId, 
                    AppleContentFormatId,
                    PodcastName, EpisodeName, Description, Keywords,
                    ContentUrl, CustomTopic
                   FROM dbo.ContextualCategories
                   WHERE PublisherId = {} AND Active = 'False' AND Lock = 0
                   ORDER BY Id DESC
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
            podcast['custom_topic'] = podcast_db[10]
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
    
    def get_custom_topic_id(self, custom_topic):
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT Id
                   FROM dbo.CustomTopics
                   WHERE CustomTopic = '{}'
                """.format(custom_topic.lower())
        cursor = conn.cursor()
        cursor.execute(query)
        custom_topic_id = cursor.fetchone()[0]
        cursor.close()
        return custom_topic_id

    def get_custom_topic_status(self, custom_topic):
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT StartDate, EndDate
                   FROM dbo.CustomTopics
                   WHERE CustomTopic = '{}'
                """.format(custom_topic.lower())
        cursor = conn.cursor()
        cursor.execute(query)
        start_date, end_date = cursor.fetchone()
        cursor.close()
        return start_date <= datetime.now() <= end_date

    def get_all_active_custom_status(self):
        custom_topics_active = []
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT Id, TotalScore
                   FROM dbo.CustomTopics
                   WHERE '{}' BETWEEN StartDate AND EndDate
                """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            custom_topics_active.append((row[0], row[1]))
        return custom_topics_active

    def get_podcast_custom_topic_keyword(self, custom_topic_id):
        keywords = []
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT Keyword, Score
                   FROM dbo.CustomTopicsKeywords
                   WHERE CustomTopicId = {}
                """.format(custom_topic_id)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            keywords.append((row[0], row[1]))
        cursor.close()
        return keywords

    def get_podcast_custom_topic_keyword_custom_topic(self, custom_topic):
        custom_topic_info = {
            'custom_topic': custom_topic,
            'keyword': []
        }
        conn = pyodbc.connect(self.conn_dmp)
        query = """SELECT CustomTopicId, TotalScore, Keyword, Score
                   FROM dbo.CustomTopics
                   JOIN dbo.CustomTopicsKeywords ON dbo.CustomTopics.Id = dbo.CustomTopicsKeywords.CustomTopicId
                   WHERE dbo.CustomTopics.CustomTopic = '{}'
                """.format(custom_topic.lower())
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            custom_topic_info['id'] = row[0]
            custom_topic_info['total_score'] = row[1]
            custom_topic_info['keyword'].append((row[2], row[3]))
        return custom_topic_info
    
#---------------------------------------------------------------------------------------------------#

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

    def write_custom_topic(self, custom_topic):
        conn = pyodbc.connect(self.conn_dmp)
        query = """INSERT INTO dbo.CustomTopics
                    (CustomTopic, TotalScore, Active, 
                    StartDate, EndDate, CreatedDate, UpdatedDate)
                   VALUES
                    ('{}', {}, 'True', '{}', '{}', '{}', '{}')
                """.format(
                    custom_topic['custom_topic'],
                    custom_topic['total_score'],
                    custom_topic['start_date'],
                    custom_topic['end_date'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # CreatedDate
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # UpdatedDate
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.execute('SELECT @@IDENTITY')
        last_custom_id = cursor.fetchone()[0]
        cursor.close()
        return last_custom_id
    
    def write_custom_topic_keyword(self, values):
        conn = pyodbc.connect(self.conn_dmp)
        query = """INSERT INTO dbo.CustomTopicsKeywords
                    (Keyword, Score, CustomTopicId, CreatedDate, UpdatedDate)
                   VALUES
                    (?, ?, ?, ?, ?)
                """
        cursor = conn.cursor()
        cursor.executemany(query, values)
        conn.commit()
        cursor.close()

    def write_custom_topic_podcast(self, custom_topic_id, podcast_id, total_score, keyword_match):
        conn = pyodbc.connect(self.conn_dmp)
        query = """INSERT INTO dbo.CustomTopicsPodcasts
                    (CustomTopicId, PodcastId, TotalScore, KeywordMatch, CreatedDate, UpdatedDate)
                   VALUES
                    ({}, {}, {}, '{}', '{}', '{}')
                """.format(
                    custom_topic_id,
                    podcast_id,
                    total_score,
                    str(json.dumps(keyword_match, ensure_ascii = False)),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # CreatedDate
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S') # UpdatedDate
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()

#---------------------------------------------------------------------------------------------------#

    def update_podcast_lock(self, id, lock = 1):
        conn = pyodbc.connect(self.conn_dmp)
        query = """UPDATE dbo.ContextualCategories
                   SET Lock = {}, UpdatedDate = '{}'
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
                        TopicsMatch = '{}',
                        UpdatedDate = '{}',
                        Active = 'True',
                        Lock = -1
                   WHERE Id = {} AND 
                        ShowId = '{}' AND 
                        EpisodeId = '{}' AND 
                        PublisherId = '{}'
                """.format(
                    data['AppleContentFormatId'],
                    data['IabV2ContentFormatId'],
                    data['TransLink'],
                    str(data['Topics']),
                    str(data['TopicsMatch']),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # UpdatedDate
                    data['Id'],
                    data['ShowId'], 
                    data['EpisodeId'], 
                    data['PublisherId']
                )
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        cursor.close()
