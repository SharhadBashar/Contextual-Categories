import os
import sys
import pytest
import platform
from pprint import pprint
from datetime import datetime
from termcolor import colored

from s3 import S3
from constants import *

'''
if __name__ == '__main__':
    try:
        command = sys.argv[1].lower()
    except IndexError:
        print('Type -r for read test or -w for write test')
        quit()

    s3 = S3()
    if (command == '-r'):
        try:
            s3.print_buckets()
            print()
            for bucket in s3.get_buckets(s3):
                print('Bucket Name:', bucket)
                s3.print_files_in_buckets(bucket)
        except Exception as e:
            print('Read not successful. Fill error traceback as follows:')
            print(e)
    elif (command == '-w'):
        now = datetime.now()
        f = open(os.path.join(PATH_DEBUG, 'test_aws.txt'), 'w')
        f.write(now)
        f.close()
        # response = s3.upload_file(os.path.join(PATH_DEBUG, 'test_aws.pkl'), S3_TRANSCRIBE['name'])
        # if (response):
        #     print('Write successful. WOOHOO!!!')
        # else:
        #     print('Write not successful. Fill error traceback above')
    else:
        print('Type -r for read test or -w for write test')
        quit()
'''

class Test:
    def __init__(self, functionality, type = ''):
        if (functionality == 'all'):
            self.all()
        elif (functionality == 'aws'):
            assert self.aws(type) == True
    
    def all(self):
        print('all')
        
    def aws(self, test_type = ''):
        s3 = S3()
        if (test_type == 'read'):
            response = s3.check_file(S3_CONTEXTUAL_WEB_API['name'], TEST_AWS_READ_FILE)
            return response['ResponseMetadata']['HostId'] != None
        elif(test_type == 'write'):
            now = datetime.now()
            f = open(os.path.join(PATH_DEBUG, now + TXT), 'w')
            f.write(now)
            f.close()
            s3.check_file(S3_CONTEXTUAL_WEB_API['name'], TEST_AWS_READ_FILE)

def print_start():
    cols, _ = os.get_terminal_size()
    print(os)

if __name__ == '__main__':
    tests = list(TESTS.keys())
    try:
        test = sys.argv[1].lower()
    except Exception as e:
        print('Please enter a functionality to test. Refer to the instructions below:')
        print(TEST_CONSOLE_MISTAKE)
        quit()
    try:
        test_type = sys.argv[2].lower()
    except:
        test_type = None
        
    print_start()
    if (test == '-a'):
        ans = input('You are about to run all unit tests. Do you want to proceed? {}: '.format(colored('[Y/n]', attrs = ['bold'])))
        if (ans.lower() == 'y'):
            Test('all')
            quit()
    if (test in tests):
        Test(test)
        quit()
    if test_type:
        Test(test, test_type)
        quit()
    else:
        print(TEST_CONSOLE_MISTAKE)
        quit()
