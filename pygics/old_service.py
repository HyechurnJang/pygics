# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 19. OLD
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import os
import re
import sys
import json
import uuid
import types
import urllib
import inspect
import requests
import platform
import logging
import logging.handlers
from jzlib import setGlobals
from mimetypes import MimeTypes
from gevent.pywsgi import WSGIServer
from .task import Burst
from .service_impl import __install_module__, __uninstall_module__

class ENV:
    
    UUID = None
    EXPORT = {}
     
    class DIR:
         
        ROOT = os.path.split(os.path.abspath(__file__))[0]
        SVC = None
        MOD = None
    
    class NET:
        
        IP = None
        PORT = None
    
    class LOG:
        
        PYGICS = None
        MODULE = None
    
    class SYS:
        
        OS = None
        DIST = None
        VER = None
    
    class MOD:
        
        PRIO = []
        DESC = {}
        
        @classmethod
        def save(cls):
            with open(ENV.DIR.SVC + '/modules.json', 'w') as fd:
                fd.write(json.dumps({'prio' : ENV.MOD.PRIO, 'desc' : ENV.MOD.DESC}))
        
        @classmethod
        def install(cls, path): __install_module__(path)
        
        @classmethod
        def uninstall(cls, name): __uninstall_module__(name)
    
    @classmethod
    def init(cls, ip, port, root):
        cls.NET.IP = ip
        cls.NET.PORT = port
        
        cls.DIR.ROOT = root
        cls.DIR.SVC = cls.DIR.ROOT + '/__run__'
        cls.DIR.MOD = cls.DIR.SVC + '/modules'
        if not os.path.exists(cls.DIR.SVC): os.mkdir(cls.DIR.SVC)
        if not os.path.exists(cls.DIR.MOD): os.mkdir(cls.DIR.MOD)
        
        l_os, l_ver, _ = platform.dist()
        w_os, w_ver, _, _ = platform.win32_ver()
        if l_os:
            cls.SYS.OS = 'linux'
            cls.SYS.DIST = l_os.lower()
            cls.SYS.VER = l_ver
        elif w_os:
            cls.SYS.OS = 'windows'
            cls.SYS.DIST = w_os.lower()
            cls.SYS.VER = w_ver
        else:
            cls.SYS.OS = 'unknown'
            cls.SYS.DIST = 'unknown'
            cls.SYS.VER = 'unknown'
        
        if os.path.exists(cls.DIR.SVC + '/service.uuid'):
            with open(cls.DIR.SVC + '/service.uuid') as fd: cls.UUID = fd.read()
        else:
            cls.UUID = str(uuid.uuid4()).replace('-', '')
            with open(cls.DIR.SVC + '/service.uuid', 'w') as fd: fd.write(cls.UUID)
        if not os.path.exists(cls.DIR.SVC + '/modules.json'):
            with open(cls.DIR.SVC + '/modules.json', 'w') as fd: fd.write(json.dumps({'prio' : [], 'desc' : []}))
        
        class __PygicsModuleLogRedirect__:
            def __init__(self, logger): self.logger = logger
            def write(self, msg):
                if msg == '\n': pass
                else: self.logger.info(msg)
        
        cls.LOG.PYGICS = logging.Logger('pygics')
        cls.LOG.MODULE = logging.Logger('pygics-module')
        log_scrn = logging.StreamHandler()
        plog_file = logging.handlers.TimedRotatingFileHandler(cls.DIR.SVC + '/pygics.log', when='D', backupCount=7)
        mlog_file = logging.handlers.TimedRotatingFileHandler(cls.DIR.SVC + '/modules.log', when='D', backupCount=7)
        mlog_file.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        cls.LOG.PYGICS.addHandler(log_scrn)
        cls.LOG.PYGICS.addHandler(plog_file)
        cls.LOG.MODULE.addHandler(log_scrn)
        cls.LOG.MODULE.addHandler(mlog_file)
        sys.stdout = __PygicsModuleLogRedirect__(cls.LOG.MODULE)
        
        setGlobals(ENV=ENV, pwd=ENV.pwd, pmd=ENV.pmd)
        
        print('PYGICS-UUID : %s' % cls.UUID)
    
    @classmethod
    def pwd(cls):
        mod = inspect.getmodule(inspect.stack()[1][0])
        mod_path, _ = os.path.split(os.path.abspath(mod.__file__))
        return mod_path
    
    @classmethod
    def pmd(cls):
        mod = inspect.getmodule(inspect.stack()[2][0])
        mod_name = mod.__name__
        mod_path, _ = os.path.split(mod.__file__)
        return mod_path, mod_name
    
class ContentType:
    
    MTOBJ = MimeTypes()
    
    AppJS = 'application/javascript'
    AppJson = 'application/json'
    AppStream = 'application/octet-stream'
    AppForm = 'application/x-www-form-urlencoded'
    TextCss = 'text/css'
    TextHtml = 'text/html'
    TextPlain = 'text/plain'
    ImageJpg = 'image/jpeg'
    ImagePng = 'image/png'
    ImageGif = 'image/gif'
    ImageTiff = 'image/tiff'
    
    @classmethod
    def format(cls, val): return ('Content-Type', val)
    
    @classmethod
    def getType(cls, path):
        mimetype, _ = cls.MTOBJ.guess_type(path)
        if not mimetype: return ContentType.AppStream
        return mimetype

class Request:
    
    COOKIE_PARSER = re.compile('(?P<key>[\w\-\.]+)=(?P<val>\S+)', re.UNICODE)
    QUERY_PARSER = re.compile('(?P<key>[\w\%]+)="?(?P<val>[\w\.\-\:\[\]]*)"?', re.UNICODE)
    XFORM_PARSER = re.compile('(?P<key>[\w]+)=(?P<val>[\W\w\s]*)', re.UNICODE)
    
    def __init__(self, req):
        self.request = req
        self.method = req['REQUEST_METHOD']
        self.path = req['PATH_INFO']
        self.headers = {}
        self.cookies = {}
        self._cookies = {}
        self.kargs = {}
        # Headers
        for key in sorted(req.keys()):
            if 'HTTP_' in key: self.headers[key.replace('HTTP_', '')] = req[key]
        # Cookies
        if 'COOKIE' in self.headers:
            cookies = self.headers['COOKIE'].split(';')
            for cookie in cookies:
                kv = Request.COOKIE_PARSER.match(cookie)
                if kv: self.cookies[kv.group('key')] = kv.group('val')
        # Query
        query_split = req['QUERY_STRING'].split('&')
        for query in query_split:
            kv = Request.QUERY_PARSER.match(urllib.unquote_plus(query).decode('utf-8'))
            if kv:
                k = kv.group('key')
                self.kargs[k] = kv.group('val')
        # Data
        if self.method in ['POST', 'PUT']:
            raw_data = req['wsgi.input'].read()
            if 'CONTENT_TYPE' in req: content_type = req['CONTENT_TYPE'].lower()
            else: content_type = ContentType.TextPlain
            if ContentType.AppJson in content_type: self.data = json.loads(raw_data)
            elif ContentType.AppForm in content_type:
                self.data = {}
                data_split = raw_data.split('&')
                for data in data_split:
                    kv = Request.XFORM_PARSER.match(urllib.unquote_plus(data).decode('utf-8'))
                    if kv: self.data[kv.group('key')] = kv.group('val')
            else: self.data = raw_data
        else: self.data = None
        # Mapping
        rns = filter(None, self.path.split('/'))
        ref = ENV.EXPORT
        for rn in rns:
            if rn in ref: ref = ref[rn]
            elif '__methods__' in ref and self.method in ref['__methods__']: break
            else: raise Response.NotFound()
        if '__methods__' not in ref: raise Response.NotFound()
        self.api = ref['__methods__'][self.method]
        self.url = ref['__export_url__']
        self.content_type = ref['__content_type__']
        if self.path == self.url: self.args = []
        else: self.args = filter(None, re.sub(self.url, '', self.path, 1).split('/'))
    
    def setCookie(self, key, val): self._cookies[key] = val
        
class Response:
    
    class __HTTP__(Exception):
        
        def __init__(self, status, headers, data):
            Exception.__init__(self)
            self.status = status
            self.headers = headers
            self.data = data
    
    class __ERR__(__HTTP__):
        
        def __init__(self, status, headers, data):
            headers.append(ContentType.format(ContentType.AppJson))
            Response.__HTTP__.__init__(self, status, headers, json.dumps({'error' : data}))
    
    class OK(__HTTP__): #200
        def __init__(self, headers=[], data='ok'):
            Response.__HTTP__.__init__(self, '200 OK', headers, data)
            
    class Redirect(__HTTP__): #302
        def __init__(self, url, headers=[], data='redirect'):
            headers.append(('Location', url))
            Response.__HTTP__.__init__(self, '302 Found', headers, data)
    
    class BadRequest(__ERR__): #400
        def __init__(self, headers=[], data='bad request'):
            Response.__ERR__.__init__(self, '400 Bad Request', headers, data)
    
    class Unauthorized(__ERR__): #401
        def __init__(self, headers=[], data='Unauthorized'):
            headers.append(('WWW-Authenticate', 'Basic realm="pygics"'))
            Response.__ERR__.__init__(self, '401 Unauthorized', headers, data)
    
    class NotFound(__ERR__): #404
        def __init__(self, headers=[], data='not found'):
            Response.__ERR__.__init__(self, '404 Not Found', headers, data)
    
    class ServerError(__ERR__): #500
        def __init__(self, headers=[], data='internal server error'):
            Response.__ERR__.__init__(self, '500 Internal Server Error', headers, data)

def server(ip,
           port=80,
           *modules):
    
    #===========================================================================
    # Initial Setup
    #===========================================================================
    _caller = inspect.getmodule(inspect.stack()[1][0])
    ENV.init(ip, port, os.path.split(os.path.abspath(_caller.__file__))[0])
    
    #===========================================================================
    # Define Built-in Functions
    #===========================================================================
    def __pygics_wsgi_application__(req, res):
        try: req = Request(req)
        except Response.__HTTP__ as e:
            res(e.status, e.headers)
            return [e.data]
        except Exception as e:
            ENV.LOG.MODULE.exception(str(e))
            res('400 Bad Request', [('Content-Type', ContentType.AppJson)])
            return [json.dumps({'error' : str(e)})]
        return [req.api(req, res)]

    #===========================================================================
    # Management Admin Rest APIs
    #===========================================================================
    @rest('GET', 'module')
    def get_module(req):
        return {'prio' : ENV.MOD.PRIO, 'desc' : ENV.MOD.DESC}
    
    @rest('POST', 'module')
    def upload_module(req, name):
        if 'PYGICS_UUID' not in req.headers or req.headers['PYGICS_UUID'] != ENV.UUID: raise Exception('incorrect uuid')
        raw_file = '%s/%s.raw' % (ENV.DIR.MOD, name)
        with open(raw_file, 'wb') as fd: fd.write(req.data)
        __install_module__(raw_file)
        return {'result': 'success'}
            
    @rest('DELETE', 'module')
    def delete_module(req, name):
        if 'PYGICS_UUID' not in req.headers or req.headers['PYGICS_UUID'] != ENV.UUID: raise Exception('incorrect uuid')
        __uninstall_module__(name)
        return {'result': 'success'}
    
    @rest('GET', 'repo')
    def get_repo(req):
        app, exp = Burst().register(
            requests.get, 'https://api.github.com/users/pygics-app/repos').register(
            requests.get, 'https://api.github.com/users/pygics-app-exp/repos').do()
        result = {'app' : [], 'exp' : []}
        if app.status_code == 200:
            repos = app.json()
            for repo in repos:
                result['app'].append({'name' : repo['name'], 'description' : repo['description']})
        if exp.status_code == 200:
            repos = exp.json()
            for repo in repos:
                result['exp'].append({'name' : repo['name'], 'description' : repo['description']})
        return result
    
    @rest('POST', 'repo')
    def install_repo(req, repo, name, branch='master'):
        if 'PYGICS_UUID' not in req.headers or req.headers['PYGICS_UUID'] != ENV.UUID: raise Exception('incorrect uuid')
        if repo not in ['app', 'exp']: raise Exception('incorrect repository name')
        __install_module__('%s::%s::%s' % (repo, name, branch))
        return {'result': 'success'}
    
    print('module pygics is installed')
    
    #===========================================================================
    # Load Modules
    #===========================================================================
    try:
        with open(ENV.DIR.SVC + '/modules.json', 'r') as fd: upload_modules = json.loads(fd.read())
    except Exception as e:
        ENV.LOG.MODULE.exception(str(e))
    else:
        try:
            for module in modules: __install_module__(module)
            for name in upload_modules['prio']:
                __install_module__(upload_modules['desc'][name]['path'])
        except Exception as e:
            ENV.LOG.MODULE.exception(str(e))
        else:
            
    #===========================================================================
    # Run Server
    #===========================================================================
    
            try:
                WSGIServer((ip, port),
                           application=__pygics_wsgi_application__,
                           log=ENV.LOG.PYGICS,
                           error_log=ENV.LOG.PYGICS).serve_forever()
            except (KeyboardInterrupt, SystemExit): print('pygics interrupted')
            except: raise

def export(method, url, content_type=None, **plugins):
    def api_wrapper(func):
        modules = []
        for name, option in plugins.items():
            try:
                module = __import__(name)
                modules.append((module, option))
            except Exception as e: print('loading api module %s failed' % name)
            else: print('loading api module %s success' % name)
        
        def decofunc(req, res):
            try:
                # Pre-Running Plugins
                for module in modules: module[0].api_plugin(req, res, **module[1])
                # Run API Processing
                data = func(req, *req.args, **req.kargs)
                # Deciding Content Type
                if isinstance(data, dict) or isinstance(data, list):
                    data = json.dumps(data)
                    content_type = ContentType.AppJson if req.content_type == None else req.content_type
                elif isinstance(data, str) or isinstance(data, unicode):
                    content_type = ContentType.TextPlain if req.content_type == None else req.content_type
                elif isinstance(data, int) or isinstance(data, float):
                    data = str(data)
                    content_type = ContentType.TextPlain if req.content_type == None else req.content_type
                elif isinstance(data, types.FileType):
                    fd = data
                    content_type = ContentType.getType(fd.name) if req.content_type == None else req.content_type
                    data = fd.read()
                    fd.close()
                elif not data:
                    data = ''
                    content_type = ContentType.TextPlain if req.content_type == None else req.content_type
                else:
                    content_type = ContentType.AppStream if req.content_type == None else req.content_type
            # Exception Processing
            except Response.__HTTP__ as e:
                res(e.status, e.headers)
                return e.data
            except TypeError as e:
                ENV.LOG.MODULE.exception(str(e))
                res('400 Bad Request', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            except Exception as e:
                ENV.LOG.MODULE.exception(str(e))
                res('500 Internal Server Error', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            # Build Response
            headers = [('Content-Type', content_type)]
            if req._cookies:
                for k, v in req._cookies.items(): headers.append(('Set-Cookie', '%s=%s' % (k, v)))
            res('200 OK', headers)
            return data
        
        module_name = func.__module__
        func_name = func.__name__
        method_upper = method.upper()
        if method_upper not in ['GET', 'POST', 'PUT', 'DELETE']: raise Exception('method %s is not permitted' % method)
        if url[0] != '/':
            if module_name == '__main__': dn = '/' + url
            elif module_name == 'pygics.service': dn = '/pygics/' + url 
            else: dn = '/%s/%s' % (module_name, url)
        else:
            dn = url
        rns = filter(None, dn.split('/'))
        ref = ENV.EXPORT
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        if '__methods__' not in ref: ref['__methods__'] = {}
        ref['__methods__'][method_upper] = decofunc
        ref['__export_url__'] = dn
        ref['__content_type__'] = content_type
        print('register api <%s:%s> link to <%s.%s>' % (method_upper, dn, module_name, func_name))
        return decofunc
    
    return api_wrapper

def rest(method, url, **plugins):
    return export(method, url, content_type=ContentType.AppJson, **plugins)
