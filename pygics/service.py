# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 2. 15.
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import os
import io
import re
import sys
import json
import urllib
import traceback
from gevent.pywsgi import WSGIServer
from watchdog_gevent import Observer
from watchdog.events import FileSystemEventHandler
from .common import logDebug, logError, load, dumpJson
from .struct import PygObj, Inventory, singleton
from .constant import HttpMethodType, HttpContentType, HttpResponseType


def create_service():

    @singleton
    class Service(Inventory):
        
        def __init__(self):
            Inventory.__init__(self, tracking=False)
        
        def register(self, action):
            ref = self
            for name in action._pyg_action_path:
                children = +ref
                if name in children:
                    ref = children[name]
                else:
                    ref = Inventory(tracking=False).setParent(ref, name)
            action.setParent(ref, action._pyg_action_method)
            logDebug('[Pygics Service] Register > URL=%s:%s > Action=%s.%s' % (action._pyg_action_method, action._pyg_action_url, action._pyg_action_module, action._pyg_action_fname))
        
        def search(self, request):
            ref = self
            for name in request.path:
                children = +ref
                if name in children:
                    ref = children[name]
                else: break
            if hasattr(ref, request.method):
                return (+ref)[request.method]
            else: HttpResponseType.NotFound()


class Action(Inventory):
    
    def __init__(self, func, method, url):
        Inventory.__init__(self, tracking=False)
        self._pyg_action_func = func
        self._pyg_action_fname = func.__name__
        self._pyg_action_module = func.__module__
        self._pyg_action_method = method.upper()
        if self._pyg_action_method not in HttpMethodType.SupportList:
            raise Exception('could not register unsupported method %s' % self._pyg_action_method)
        self._pyg_action_url = url
        self._pyg_action_path = list(filter(None, url.split('/')))
    
    def __wsi__(self, req):
        try:
            content_type, data = self.__run__(req)
        except HttpResponseType.__ERROR__ as e:
            return e
        except TypeError as e:
            return HttpResponseType.BadRequest(str(e), exception=False)
        except Exception as e:
            traceback.print_exc()
            logError('[Pygics Action] %s.%s > %s' % (self._pyg_action_module, self._pyg_action_fname, str(e)))
            return HttpResponseType.ServerError(str(e), exception=False)
        else:
            headers = [('Content-Type', content_type)]
            if req.headers_add:
                for k, v in req.headers_add.items(): headers.append((k, v))
            if req.cookies_add:
                for k, v in req.cookies_add.items(): headers.append(('Set-Cookie', '%s=%s' % (k, v)))
            return HttpResponseType.OK(data, headers)
    
    def __run__(self, req): pass


class Request:
     
    COOKIE_PARSER = re.compile('(?P<key>[\w\-\.]+)=(?P<val>\S+)', re.UNICODE)
    QUERY_PARSER = re.compile('(?P<key>[\w\%]+)="?(?P<val>[\w\.\-\:\[\]]*)"?', re.UNICODE)
    XFORM_PARSER = re.compile('(?P<key>[\w]+)=(?P<val>[\W\w\s]*)', re.UNICODE)
     
    def __init__(self, request):
        self.request = request
        self.method = request['REQUEST_METHOD']
        self.url = request['PATH_INFO']
        self.path = list(filter(None, self.url.split('/')))
        self.headers = {}
        self.headers_add = {}
        self.cookies = {}
        self.cookies_add = {}
        self.kargs = {}
        
        # Action
        self.action = Pygics.Service.search(self)
         
        # Headers
        for key in request.keys():
            if 'HTTP_' in key: self.headers[key.replace('HTTP_', '')] = request[key]
        
        # Cookies
        if 'COOKIE' in self.headers:
            cookies = self.headers['COOKIE'].split(';')
            for cookie in cookies:
                kv = Request.COOKIE_PARSER.match(cookie)
                if kv: self.cookies[kv.group('key')] = kv.group('val')
        
        # Array Parameter
        self.args = self.path[len(self.action._pyg_action_path):]
        
        # Query Parameter
        for query in request['QUERY_STRING'].split('&'):
            if not query: continue
            kv = Request.QUERY_PARSER.match(urllib.parse.unquote_plus(query))
            if kv: self.kargs[kv.group('key')] = kv.group('val')
        
        # Data
        if self.method in ['POST', 'PUT', 'PATCH']:
            raw_data = request['wsgi.input'].read()
            if 'CONTENT_TYPE' in request:
                content_type = request['CONTENT_TYPE'].lower()
                if HttpContentType.AppJson in content_type: self.data = json.loads(raw_data)
                elif HttpContentType.AppForm in content_type:
                    self.data = {}
                    data_split = raw_data.split('&')
                    for data in data_split:
                        kv = Request.XFORM_PARSER.match(urllib.parse.unquote_plus(data))
                        if kv: self.data[kv.group('key')] = kv.group('val')
                else: self.data = raw_data
            else: self.data = raw_data
        else: self.data = None
     
    def setCookie(self, key, val):
        self.cookies_add[key] = val
    
    def setHeader(self, key, val):
        self.headers_add[key] = val


class File(PygObj):
    
    def __init__(self, path=None):
        self.path = path
        if path:
            self.is_file = True
            self.content_type, self.payload = Pygics.FileCache.search(self)
        else:
            self.is_file = False
            self.content_type = HttpContentType.TextPlain
            self.payload = ''
    
    def write(self, text):
        if not self.is_file:
            self.payload = self.payload + text
        return self


def download(url):
    
    @singleton
    class FileCache(Inventory, dict):
        
        class Watcher(Inventory, Observer):
            
            def __init__(self):
                
                class FileCacheHandler(FileSystemEventHandler):
            
                    def on_modified(self, event):
                        path = event.src_path
                        with open(path, 'rb') as fd:
                            Pygics.FileCache[path] = (HttpContentType.getType(fd.name), fd.read())
                        logDebug('[Pygics FileCache] Reload > %s' % path)
                
                Observer.__init__(self)
                self._pyg_watcher_handler = FileCacheHandler()
                self.start()
            
            def register(self, path):
                self.schedule(self._pyg_watcher_handler, path=path)
        
        def search(self, file):
            path = file.path
            if path and os.path.exists(path) and os.path.isfile(path):
                path = os.path.realpath(path)
                if path in self:
                    return self[path]
                else:
                    with open(path, 'rb') as fd:
                        self[path] = (HttpContentType.getType(fd.name), fd.read())
                    Pygics.FileCache.Watcher.register(path)
                    return self[path]
            else: raise Exception('could not found file %s' % path)
        
        def __init__(self):
            Inventory.__init__(self)
            dict.__init__(self)
    
    class DownloadAction(Action):
    
        def __init__(self, func, method, url):
            Action.__init__(self, func, method, url)
        
        def __run__(self, req):
            data = self._pyg_action_func(req, *req.args, **req.kargs)
            if isinstance(data, File):
                return data.content_type, data.payload
            elif isinstance(data, io.IOBase):
                fd = data
                data = fd.read()
                content_type = HttpContentType.getType(fd.name)
                fd.close()
                return content_type, data
            else:
                HttpResponseType.ServerError('returned data is not file descriptor')
    
    def wrapper(func):
        create_service()
        Pygics.Service.register(DownloadAction(func, HttpMethodType.Get, url))
        return func
    
    return wrapper


def rest(method, url):
    
    class RestAction(Action):
    
        def __init__(self, func, method, url):
            Action.__init__(self, func, method, url)
        
        def __run__(self, req):
            data = self._pyg_action_func(req, *req.args, **req.kargs)
            if isinstance(data, dict) or isinstance(data, list):
                return HttpContentType.AppJson, dumpJson(data)
            elif not data:
                return HttpContentType.TextPlain, ''
            else:
                return HttpContentType.TextPlain, str(data)
    
    def wrapper(func):
        create_service()
        Pygics.Service.register(RestAction(func, method, url))
        return func
    
    return wrapper


def server(ip, port, *modules, **configs):
    
    #===========================================================================
    # Init Service
    #===========================================================================
    create_service()
    
    #===========================================================================
    # Start Web Default Service
    #===========================================================================
    favicon = configs['favicon'] if 'favicon' in configs else None
    static = configs['static'] if 'static' in configs else False
    
    static_path, _ = os.path.split(__file__)
    static_path = static_path + '/static'
    if favicon:
        if not os.path.exists(favicon):
            raise Exception('could not find favicon')
    else:

        @download('/favicon.ico')
        def favicon_sender(req, *path, **param):
            return File(static_path + '/favicon.ico')
    
    if static:

        @download('/pygics')
        def pygics_sender(req, *path, **param):
            path = '/'.join(path)
            if path == 'js': return File(static_path + '/pygics.js')
            elif path == 'css': return File(static_path + '/pygics.css')
            else: return File(static_path + '/%s' % path)
    
    #===========================================================================
    # Init Modules
    #===========================================================================
    for mod in modules: load(mod)
    
    #===========================================================================
    # Pygics WSGI Handler
    #===========================================================================
    def __application__(request, response):
        try:
            req = Request(request)
        except HttpResponseType.__ERROR__ as e:
            response(e.status, e.headers)
            return [e.data.encode()]
        except Exception as e:
            traceback.print_exc()
            logError('[Pygics Request] %s' % str(e))
            response('400 Bad Request', [('Content-Type', HttpContentType.AppJson)])
            return [json.dumps({'error' : str(e)}).encode()]
        
        res = req.action.__wsi__(req)
        response(res.status, res.headers)
        if isinstance(res.data, str):
            return [res.data.encode()]
        else:
            return [res.data]
        
    #===========================================================================
    # Run Server
    #===========================================================================
    try: WSGIServer((ip, port), application=__application__, log=sys.stdout).serve_forever()
    except (KeyboardInterrupt, SystemExit): logDebug('[Pygics Server] Interrupted')
    except: raise
