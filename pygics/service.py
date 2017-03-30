# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 29.
@author: HyechurnJang
'''

import os
import re
import sys
import json
from gevent.pywsgi import WSGIServer

_pygics_rest_apis = {'GET' : {}, 'POST' : {}, 'PUT' : {}, 'DELETE' : {}}

class Request:
    
    class NotFound(Exception):
        def __init__(self): Exception.__init__(self, 'method or url mismatched')
        
    def __init__(self, req):
        self.request = req
        self.method = req['REQUEST_METHOD']
        self.path = req['PATH_INFO']
        self.header = {}
        for key in sorted(req.keys()):
            if 'HTTP_' in key: self.header[key.replace('HTTP_', '')] = req[key]
        self.kwargs = {}
        qs = req['QUERY_STRING'].split('&')
        for q in qs:
            kv = re.match('(?P<key>\w+)=("|%22|%27)?(?P<val>[\w]+)("|%22|%27)?', q)
            if kv: self.kwargs[kv.group('key')] = kv.group('val')
        if self.method in ['POST', 'PUT']: self.data = json.loads(req['wsgi.input'].read())
        else: self.data = {}
        rns = filter(None, self.path.split('/'))
        rns_len = len(rns)
        ref = _pygics_rest_apis[self.method]
        for i in range(0, rns_len):
            rn = rns[i]
            if rn in ref: ref = ref[rns[i]]
            elif '__api_ref__' in ref: break
            else: raise Request.NotFound()
        self.api = ref['__api_ref__']
        self.url = ref['__api_url__']
        self.args = filter(None, re.sub(self.url, '', self.path, 1).split('/'))
        
    def __str__(self):
        return '%s : %s\nHeader : %s\nArgs : %s\nQuery : %s\nData : %s' % (self.method, self.url, self.header, self.args, self.kwargs, self.data)

def __pygics_wsgi_application__(req, res):
    try: req = Request(req)
    except Request.NotFound as e:
        res('404 Not Found', [('Content-Type', 'application/json')])
        return json.dumps({'error' : str(e)})
    except Exception as e:
        res('400 Bad Request', [('Content-Type', 'application/json')])
        return json.dumps({'error' : str(e)})
    try: return req.api(req, res)
    except Exception as e:
        res('500 Internal Server Error', [('Content-Type', 'application/json')])
        return json.dumps({'error' : str(e)})

def service(method, url):
    def api_wrapper(func):
        def decofunc(req, res):
            try: ret = func(req, *req.args, **req.kwargs)
            except TypeError:
                res('400 Bad Request', [('Content-Type', 'application/json')])
                return json.dumps({'error' : 'parameter mismatched'})
            except Exception as e:
                res('500 Internal Server Error', [('Content-Type', 'application/json')])
                return json.dumps({'error' : str(e)})
            res('200 OK', [('Content-Type', 'application/json')])
            return json.dumps(ret)
        rns = filter(None, url.split('/'))
        ref = _pygics_rest_apis[method.upper()]
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        ref['__api_url__'] = url
        ref['__api_ref__'] = decofunc
        print('[register]%s:%s ==> %s.%s()' % (method, url, func.__module__, func.__name__))
        return decofunc
    return api_wrapper

def server(listener, *file_paths):
    for file_path in file_paths:
        if os.path.isfile(file_path):
            directory, file_name = os.path.split(file_path)
            mod_name = os.path.splitext(file_name)[0]
            if directory != '': sys.path.insert(0, directory)
            __import__(mod_name)
    WSGIServer(listener, __pygics_wsgi_application__).serve_forever()
