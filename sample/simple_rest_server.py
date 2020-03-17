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

from pygics import rest, server, setEnv

history = []


@rest('GET', '/api/calculator/add')
def calc_add(req, a, b):
    '''
    calling follow as
      - GET /api/calculator/add/100/10
      - GET /api/calculator/add?a=100&b=10
    '''
    result = int(a) + int(b)
    history.append(result)
    return {'result' : result}


@rest('GET', '/api/calculator/sub')
def calc_sub(req, a, b):
    '''
    calling follow as
      - GET /api/calculator/sub/100/10
      - GET /api/calculator/sub?a=100&b=10
    '''
    result = int(a) - int(b)
    history.append(result)
    return {'result' : result}


@rest('POST', '/api/calculator/multi-add')
def calc_multi_add(req):
    '''
    calling follow as
      - POST /api/calculator/multi-add
    request body = [ NUM-1, NUM-2, NUM-3, ... NUM-N ]
    '''
    nums = req.data
    result = 0
    for num in nums:
        result += num
    history.append(result)
    return {'result' : result}


@rest('GET', '/api/calculator')
def calc_history(req, id=None):
    if id != None:
        return {'result' : {'id' : int(id), 'data' : history[int(id)]}}
    result = []
    for i in range(0, len(history)):
        result.append({'result' : {'id' : str(i), 'data' : history[i]}})
    return {'history' : result}


if __name__ == '__main__':
    server('0.0.0.0', 80)
