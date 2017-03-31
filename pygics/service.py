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
from .task import Task

_pygics_service_dir = os.path.expanduser('~') + '/.pygics'
_pygics_service_subdir = ''
_pygics_service_modules = {}
_pygics_service_rest_apis = {'GET' : {}, 'POST' : {}, 'PUT' : {}, 'DELETE' : {}}

class Request:
    
    class NotFound(Exception):
        def __init__(self): Exception.__init__(self, 'method or url mismatched')
        
    class UnsupportContentType(Exception):
        def __init__(self): Exception.__init__(self, 'unsupport content type')
    
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
        if self.method in ['POST', 'PUT']:
            raw_data = req['wsgi.input'].read()
            if 'CONTENT_TYPE' in req: content_type = req['CONTENT_TYPE']
            else: content_type = 'application/json; charset=UTF-8'
            if 'application/json' in content_type: self.data = json.loads(raw_data)
            elif 'text/plain' in content_type: self.data = raw_data
            else: raise Request.UnsupportContentType()
        else: self.data = {}
        rns = filter(None, self.path.split('/'))
        rns_len = len(rns)
        ref = _pygics_service_rest_apis[self.method]
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

def __delete_module__(mod_name):
    if mod_name == 'pygics': return
    if mod_name in _pygics_service_rest_apis['GET']: _pygics_service_rest_apis['GET'].pop(mod_name)
    if mod_name in _pygics_service_rest_apis['POST']: _pygics_service_rest_apis['POST'].pop(mod_name)
    if mod_name in _pygics_service_rest_apis['PUT']: _pygics_service_rest_apis['PUT'].pop(mod_name)
    if mod_name in _pygics_service_rest_apis['DELETE']: _pygics_service_rest_apis['DELETE'].pop(mod_name)
    if mod_name in _pygics_service_modules: _pygics_service_modules.pop(mod_name)
    if mod_name in sys.modules:
        module = sys.modules.pop(mod_name)
        for _, val in module.__dict__.items():
            if isinstance(val, Task): val.stop()
        del module
        print('[deleting]METHOD:%-40s ==> deleted' % ('/%s/*' % mod_name))
        return True
    else: return False

def __load_module__(file_path):
    if os.path.isfile(file_path):
        directory, file_name = os.path.split(file_path)
        mod_name, mod_ext = os.path.splitext(file_name)
        if mod_ext == '.py':
            if directory != '' and directory not in sys.path: sys.path.insert(0, directory)
            if mod_name not in _pygics_service_modules:
                _pygics_service_modules[mod_name] = __import__(mod_name)
            else:
                __delete_module__(mod_name)
                _pygics_service_modules[mod_name] = __import__(mod_name)
            return True
    return False

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
            return json.dumps({'result' : ret})
        if func.__module__ == '__main__': dn = url
        elif func.__module__ == 'pygics.service': dn = '/pygics/%s' % url[1:] 
        else: dn = '/%s/%s' % (func.__module__, url[1:])
        rns = filter(None, dn.split('/'))
        ref = _pygics_service_rest_apis[method.upper()]
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        ref['__api_url__'] = dn
        ref['__api_ref__'] = decofunc
        print('[register]%-6s:%-40s ==> %s.%s' % (method, dn, func.__module__, func.__name__))
        return decofunc
    return api_wrapper

def server(listener, *file_paths):
    
    @service('POST', '/module')
    def load_module(req, name):
        file_path = _pygics_service_subdir + '/' + name + '.py'
        try:
            with open(file_path, 'wb') as fd: fd.write(req.data)
        except Exception as e: return {'error' : str(e)}
        return __load_module__(file_path)
    
    @service('DELETE', '/module')
    def del_module(req, name):
        file_path_py = _pygics_service_subdir + '/' + name + '.py'
        file_path_pyc = file_path_py + 'c'
        if os.path.exists(file_path_py):
            ret = __delete_module__(name)
            os.remove(file_path_py)
        if os.path.exists(file_path_pyc): os.remove(file_path_pyc)
        return ret
    
    if not os.path.exists(_pygics_service_dir): os.mkdir(_pygics_service_dir)
    _pygics_service_subdir = _pygics_service_dir + '/%s-%s' % (listener[0].replace('.', '-'), str(str(listener[1])))
    if not os.path.exists(_pygics_service_subdir): os.mkdir(_pygics_service_subdir)
    for file_path in file_paths: __load_module__(file_path)
    file_paths = os.listdir(_pygics_service_subdir)
    for file_path in file_paths: __load_module__(_pygics_service_subdir + '/' + file_path)
    WSGIServer(listener, __pygics_wsgi_application__).serve_forever()
