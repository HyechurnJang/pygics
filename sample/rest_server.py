# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 28.
@author: HyechurnJang
'''

import pygics

#===============================================================================
# GET WITH ROOT URL
#===============================================================================
# GET:<HOST> ----> 200 OK >> {"result" : "ok"}
@pygics.service('GET', '/')
def get_type_1(req):
    return 'ok'

#===============================================================================
# GET WITH PATH
#===============================================================================
# GET:<HOST>/get_with_path ----> 200 OK >> {"result" : "ok"}
@pygics.service('GET', '/get_with_path')
def get_type_2(req):
    return 'ok'

#===============================================================================
# GET WITH ARGS
#===============================================================================
# GET:<HOST>/get_with_args ----> 400 Bad Request >> {"error" : <ERROR_MESSAGE>}
# GET:<HOST>/get_with_args/val1 ----> arg1="val1", arg2=None >> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args/val1/val2 ----> arg1="val1", arg2="val2" >> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args/val1/val2/val3 ----> 400 Bad Request : {"error" : <ERROR_MESSAGE>}
# GET:<HOST>/get_with_args?arg1=val1 ----> arg1="val1", arg2=None >> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args?arg2=val2 ----> 400 Bad Request : {"error" : <ERROR_MESSAGE>}
# GET:<HOST>/get_with_args?arg1=val1&arg2=val2 ----> arg1="val1", arg2="val2" >> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args?arg2=val2&arg1=val1 ----> arg1="val1", arg2="val2" >> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args?arg1=val1&arg2=val2&arg3=val3 ----> 400 Bad Request : {"error" : <ERROR_MESSAGE>}
@pygics.service('GET', '/get_with_args')
def get_type_3(req, arg1, arg2=None):
    return 'ok'

#===============================================================================
# GET WITH ANY ARGS
#===============================================================================
# GET:<HOST>/get_with_args ----> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args/1/2/N ----> 200 OK >> {"result" : "ok"}
# GET:<HOST>/get_with_args?a=1&b=2&N=N ----> 200 OK >> {"result" : "ok"}
@pygics.service('GET', '/get_with_anys')
def get_type_4(req, *args, **kwargs):
    return 'ok'

#===============================================================================
# POST
#===============================================================================
# POST:<HOST>/post_action ----> 200 OK >> {"result" : "ok"}
# post arguments do work same as get
# support content type : "application/json", "text/plain"
# post content is saved in "req.data"
@pygics.service('POST', '/post_action')
def post(req):
    return 'ok'

#===============================================================================
# PUT
#===============================================================================
# PUT:<HOST>/put_action ----> 200 OK >> {"result" : "ok"}
# put arguments do work same as get
# support content type : "application/json", "text/plain"
# put content is saved in "req.data"
@pygics.service('PUT', '/put_action')
def put(req):
    return 'ok'

#===============================================================================
# DELETE
#===============================================================================
# DELETE:<HOST>/delete_action ----> 200 OK >> {"result" : "ok"}
# delete arguments do work same as get
@pygics.service('DELETE', '/delete_action')
def delete(req):
    return 'ok'

#===============================================================================
# SAMPLE REST
#===============================================================================
# GET:<HOST>/sum?a=10&b=20 ----> 200 OK >> {"result" : 30}
@pygics.service('GET', '/sum')
def sum(req, a, b):
    return int(a) + int(b)

# GET:<HOST>/mul?a=10&b=20 ----> 200 OK >> {"result" : 200}
@pygics.service('GET', '/mul')
def mul(req, a, b):
    return int(a) * int(b)

#===============================================================================
# PREPARED PYGICS REST API
#===============================================================================
# Load module on runtime
# Loading file save under <USER HOME>/.pygics/<SERVICE IP & PORT NAME>/<MODULE NAME>.py
# POST:<HOST>/pygics/module?name=<MODULE NAME>
# HEADERS:CONTENT_TYPE:"text/plain"
# BODY:<PYTHON CODE STRING WRITTEN WITH PYGICS>
# success ----> 200 OK >> {"result" : true}
# failed ----> 200 OK >> {"result" : false}
#
# Delete module on runtime
# DELETE:<HOST>/pygics/module?name=<MODULE NAME>
# success ----> 200 OK >> {"result" : true}
# failed ----> 200 OK >> {"result" : false}

#===============================================================================
# RUN SERVER
#===============================================================================
# Parameters
#    Name         : Type         : Example
#   ------------------------------------ -- -- - -
#    listener     : tuple        : ('<IP OR HOSTNAME>', <PORT>)
#    *file_paths  : [string,]    : 'any/other/path/module1.py', '/from/root/path/module2.py', ...
# pygics.server(('<IP OR HOSTNAME>', <PORT>), 'any/other/path/module1.py', '/from/root/path/module2.py', ...)
pygics.server(('0.0.0.0', 80))
