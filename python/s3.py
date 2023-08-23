import os
import logging
from tqdm import tqdm
from pathlib import Path

import boto3
from boto3 import client
from botocore.exceptions import ClientError

class S3:
    def __init__(self):
        self.s3_resource = boto3.resource('s3')
        self.s3_client = boto3.client('s3')

    def get_info(self, bucket, file_name):
        return self.s3_resource.Object(bucket, file_name)

    def create_bucket(self, bucket_name, region = None):
        try:
            if region is None:
                s3_client = self.s3_client
                s3_client.create_bucket(Bucket = bucket_name)
            else:
                s3_client = boto3.client('s3', region_name = region)
                location = {'LocationConstraint': region}
                s3_client.create_bucket(Bucket = bucket_name,
                                        CreateBucketConfiguration = location)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def get_buckets(self):
        buckets = []
        response = self.s3_client.list_buckets()
        for bucket in response['Buckets']:
            buckets.append(bucket['Name'])
        return buckets

    def get_file_folders(self, bucket_name, prefix = ''):
        file_names = []
        folders = []

        default_kwargs = {
            'Bucket': bucket_name,
            'Prefix': prefix
        }
        next_token = ''

        while next_token is not None:
            updated_kwargs = default_kwargs.copy()
            if next_token != '':
                updated_kwargs['ContinuationToken'] = next_token

            response = self.s3_client.list_objects_v2(**default_kwargs)
            contents = response.get('Contents')
            if contents is None:
                return None, None
            for result in contents:
                key = result.get('Key')
                if key[-1] == '/':
                    folders.append(key)
                else:
                    file_names.append(key)

            next_token = response.get('NextContinuationToken')

        return file_names, folders
    
    def download_files(self, bucket_name, local_path, file_names, folders):
        local_path = Path(local_path)
        for folder in folders:
            folder_path = Path.joinpath(local_path, folder)
            folder_path.mkdir(parents = True, exist_ok = True)
        for file_name in file_names:
            file_path = Path.joinpath(local_path, file_name)
            file_path.parent.mkdir(parents = True, exist_ok = True)
            self.s3_client.download_file(
                bucket_name,
                file_name,
                str(file_path)
            )
            
    def download_bucket(self, bucket, download_path = None):
        if not download_path or download_path == '/':
            download_path = bucket
        if not os.path.exists(download_path):
            os.mkdir(download_path)
        files = self.s3_client.list_objects(Bucket = bucket)['Contents']
        for file in tqdm(files):
            self.s3_client.download_file(bucket, file['Key'], os.path.join(download_path, file['Key']))
            
    def download_file(self, file, bucket, download_path = None):
        if not download_path or download_path == '/':
            download_path = bucket
        if not os.path.exists(download_path):
            os.mkdir(download_path)
        self.s3_client.download_file(bucket, file, os.path.join(download_path, file))

    def upload_file(self, file_name, bucket, object_name = None):
        if object_name is None:
            object_name = os.path.basename(file_name)   
        try:
            response = self.s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def print_buckets(self):
        response = self.s3_client.list_buckets()
        print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')
            
    def print_files_in_buckets(self, bucket_name):
        print('Files in {} are:'.format(bucket_name))
        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket(bucket_name)
        for object_summary in my_bucket.objects.filter():
            print(f'-- {object_summary.key}')
        
if __name__ == '__main__':
    s3 = S3()
    s3.print_buckets()
    print()
    for bucket in s3.get_buckets(s3):
        print('Bucket Name:', bucket)
        s3.print_files_in_buckets(bucket)
