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

from pygics import rest, server


@rest('GET', '/calculator/add')
def calc_add(req, a, b):
    '''
    calling follow as
      - GET /calculator/add/100/10
      - GET /calculator/add?a=100&b=10
    '''
    return {'result' : int(a) + int(b)}


@rest('GET', '/calculator/sub')
def calc_sub(req, a, b):
    '''
    calling follow as
      - GET /calculator/sub/100/10
      - GET /calculator/sub?a=100&b=10
    '''
    return {'result' : int(a) - int(b)}


@rest('POST', '/calculator/multi-add')
def calc_multi_add(req):
    '''
    calling follow as
      - POST /calculator/multi-add
    request body = [ NUM-1, NUM-2, NUM-3, ... NUM-N ]
    '''
    nums = req.data
    result = 0
    for num in nums:
        result += num
    return {'result' : result}


if __name__ == '__main__':
    server('0.0.0.0', 80)
