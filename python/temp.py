import os
import sys
import math
import pytest
import platform
from pprint import pprint
from datetime import datetime
from termcolor import colored


def print_start():
    cols, _ = os.get_terminal_size()
    start_mess = ' test session starts '
    start_lines = '=' * round((cols - len(start_mess))/2)
    start = '{}{}{}'.format(start_lines, start_mess, start_lines)
    
    print(colored(start, attrs = ['bold']))
    
    
print_start()