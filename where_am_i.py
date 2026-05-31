import os
import sys

with open('where_am_i.txt', 'w', encoding='utf-8') as f:
    f.write('Current working dir: ' + os.getcwd() + '\n')
    f.write('Python executable: ' + sys.executable + '\n')
    f.write('File list: ' + str(os.listdir('.')) + '\n')
