# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 3. 17..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

from pygics import download, File, server


@download('/modules')
def file_download_from_modules_directory(req, *path):
    '''
    calling follow as
      - GET /modules/about.py
    '''
    path = '/'.join(path)
    return File('modules/{}'.format(path))


if __name__ == '__main__':
    server('0.0.0.0', 80)
    
