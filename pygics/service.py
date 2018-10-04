# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 20.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import os
import io
import re
import sys
import uuid
import json
import urllib
import inspect
from mimetypes import MimeTypes
from gevent.pywsgi import WSGIServer
from logging import Logger, StreamHandler, Formatter
from logging.handlers import TimedRotatingFileHandler
from jzlib import getPlatform, setGlobals
from .service_impl import *

class __ENV__:
    UUID = None
    LOG = None
    
    @classmethod
    def PWD(self):
        try:
            mod = inspect.getmodule(inspect.stack()[1][0])
            mod_path, _ = os.path.split(os.path.abspath(mod.__file__))
            return mod_path
        except: pass
        return ''
    
    @classmethod
    def PMD(self):
        for i in [2, 1]:
            try: mod = inspect.getmodule(inspect.stack()[i][0])
            except: pass
            else: break
        mod_name = mod.__name__
        mod_path, _ = os.path.split(mod.__file__)
        return (mod_path, mod_name)
    
    class URI:
        MAP = {}
        
        @classmethod
        def register(cls, logic, exporter, method, url, content_type=None):
            if hasattr(logic, '__logic__'): logic = logic.__logic__
            module = logic.__module__
            logic_name = logic.__name__
            method = method.upper()
            if method not in ['GET', 'POST', 'PUT', 'DELETE']: raise Exception('method %s is not incorrect' % method)
            if url[0] != '/':
                if module == '__main__': dn = '/' + url
                else: dn = '/%s/%s' % (module.replace('.', '/'), url)
            else: dn = url
            rns = list(filter(None, dn.split('/')))
            ref = __ENV__.URI.MAP
            for rn in rns:
                if rn not in ref: ref[rn] = {}
                ref = ref[rn]
            if '__method__' not in ref: ref['__method__'] = {}
            ref['__method__'][method] = exporter
            ref['__export_url__'] = dn
            ref['__content_type__'] = content_type
            print('register uri <%s:%s> link to <%s.%s(...)>' % (method, dn, module, logic_name))
    
    class MOD:
        LIST = []
        DESC = {}
        
        @classmethod
        def install(cls, path):
            if path in __ENV__.MOD.LIST: return
            kv = re.match('\s*(?P<module>[\w\.\-\:\/]+)', path)
            if kv != None: path = kv.group('module')
            else: return []
            if re.search('^yum::', path): installYum(path)
            elif re.search('^apt::', path): installApt(path)
            elif re.search('^pip::', path): installPip(path)
            elif re.search('^(mod|app|exp)::', path): installRepo(path)
            elif re.search('^zip::', path): installZip(path)
            elif re.search('^dir::', path): installDir(path)
            elif re.search('^py::', path): installPy(path)
            else: installPath(path)
        
        @classmethod
        def register(cls, path, type, name, ver):
            __ENV__.MOD.LIST.append(path)
            __ENV__.MOD.DESC[path] = {'type' : type, 'name' : name, 'ver' : ver}
            with open(__ENV__.DIR._MOD_FILE_, 'w') as fd: fd.write(json.dumps({'list' : __ENV__.MOD.LIST, 'desc' : __ENV__.MOD.DESC}))
        
        @classmethod
        def unregister(cls, path):
            __ENV__.MOD.LIST.pop(path)
            __ENV__.MOD.DESC.pop(path)
            with open(__ENV__.DIR._MOD_FILE_, 'w') as fd: fd.write(json.dumps({'list' : __ENV__.MOD.LIST, 'desc' : __ENV__.MOD.DESC}))
        
        @classmethod
        def getRegistered(cls):
            with open(__ENV__.DIR._MOD_FILE_, 'r') as fd: return json.loads(fd.read())
    
    class SYS:
        TYPE = None
        DIST = None
        VER = None
    
    class NET:
        IP = None
        PORT = None
    
    class DIR:
        ROOT = None
        PYGICS = None
        RUN = None
        MOD = None
        _UID_FILE_ = None
        _MOD_FILE_ = None
        _LOG_FILE_ = None

class ContentType:
     
    __MTOBJ__ = MimeTypes()
     
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
    def getType(cls, path):
        mimetype, _ = cls.__MTOBJ__.guess_type(path)
        if not mimetype: return ContentType.AppStream
        return mimetype
 
class Request:
     
    COOKIE_PARSER = re.compile('(?P<key>[\w\-\.]+)=(?P<val>\S+)', re.UNICODE)
    QUERY_PARSER = re.compile('(?P<key>[\w\%]+)="?(?P<val>[\w\.\-\:\[\]]*)"?', re.UNICODE)
    XFORM_PARSER = re.compile('(?P<key>[\w]+)=(?P<val>[\W\w\s]*)', re.UNICODE)
     
    def __init__(self, request):
        self.request = request
        self.method = request['REQUEST_METHOD']
        self.path = request['PATH_INFO']
        self.headers = {}
        self.cookies = {}
        self.cookies_new = {}
        self.kargs = {}
         
        # Headers
        for key in request.keys():
            if 'HTTP_' in key: self.headers[key.replace('HTTP_', '')] = request[key]
         
        # Cookies
        if 'COOKIE' in self.headers:
            cookies = self.headers['COOKIE'].split(';')
            for cookie in cookies:
                kv = Request.COOKIE_PARSER.match(cookie)
                if kv: self.cookies[kv.group('key')] = kv.group('val')
         
        # Query
        query_split = request['QUERY_STRING'].split('&')
        for query in query_split:
            if not query: continue
            kv = Request.QUERY_PARSER.match(urllib.unquote_plus(query).decode('utf-8'))
            if kv: self.kargs[kv.group('key')] = kv.group('val')
             
        # URL Mapping
        rns = list(filter(None, self.path.split('/')))
        ref = ENV.URI.MAP
        
        for rn in rns:
            if rn in ref: ref = ref[rn]
            elif '__method__' in ref and self.method in ref['__method__']: break
            else: raise Response.NotFound()
        if '__method__' not in ref: raise Response.NotFound()
        self.api = ref['__method__'][self.method]
        self.url = ref['__export_url__']
        self.content_type = ref['__content_type__']
        if self.path == self.url: self.args = []
        else: self.args = list(filter(None, re.sub(self.url, '', self.path, 1).split('/')))
        
        # Data
        if self.method in ['POST', 'PUT']:
            raw_data = request['wsgi.input'].read()
            if 'CONTENT_TYPE' in request: content_type = request['CONTENT_TYPE'].lower()
            else: content_type = self.content_type
            if ContentType.AppJson in content_type: self.data = json.loads(raw_data)
            elif ContentType.AppForm in content_type:
                self.data = {}
                data_split = raw_data.split('&')
                for data in data_split:
                    kv = Request.XFORM_PARSER.match(urllib.unquote_plus(data).decode('utf-8'))
                    if kv: self.data[kv.group('key')] = kv.group('val')
            else: self.data = raw_data
        else: self.data = None
     
    def setCookie(self, key, val): self.cookies_new[key] = val
 
class Response:
     
    class __HTTP__(Exception):
         
        def __init__(self, status, headers, data):
            Exception.__init__(self)
            self.status = status
            self.headers = headers
            self.data = data
     
    class __ERR__(__HTTP__):
         
        def __init__(self, status, headers, data):
            headers.append(('Content-Type', ContentType.AppJson))
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

class PlugIn:
    
    def __prev__(self, req, res): pass
    def __post__(self, req, res, ret): return ret

def environment(root=None):
    if 'ENV' in __builtins__: return
    if root: __ENV__.DIR.ROOT = root
    else: __ENV__.DIR.ROOT = os.path.split(os.path.abspath(inspect.getmodule(inspect.stack()[1][0]).__file__))[0]
    __ENV__.DIR.PYGICS = __ENV__.DIR.ROOT + '/__pygics__'
    __ENV__.DIR.RUN = __ENV__.DIR.PYGICS + '/run'
    __ENV__.DIR.MOD = __ENV__.DIR.PYGICS + '/mod'
    __ENV__.DIR._UID_FILE_ = __ENV__.DIR.PYGICS + '/service.uuid'
    __ENV__.DIR._MOD_FILE_ = __ENV__.DIR.PYGICS + '/modules.json'
    __ENV__.DIR._LOG_FILE_ = __ENV__.DIR.PYGICS + '/pygics.log'
    if not os.path.exists(__ENV__.DIR.PYGICS): os.mkdir(__ENV__.DIR.PYGICS)
    if not os.path.exists(__ENV__.DIR.RUN): os.mkdir(__ENV__.DIR.RUN)
    if not os.path.exists(__ENV__.DIR.MOD): os.mkdir(__ENV__.DIR.MOD)
    
    __ENV__.SYS.TYPE, __ENV__.SYS.DIST, __ENV__.SYS.VER = getPlatform()
    
    if os.path.exists(__ENV__.DIR._UID_FILE_):
        with open(__ENV__.DIR._UID_FILE_, 'r') as fd: __ENV__.UUID = fd.read()
    else:
        __ENV__.UUID = str(uuid.uuid4())
        with open(__ENV__.DIR._UID_FILE_, 'w') as fd: fd.write(__ENV__.UUID)
    
    if not os.path.exists(__ENV__.DIR._MOD_FILE_):
        with open(__ENV__.DIR._MOD_FILE_, 'w') as fd: fd.write(json.dumps({'list' : [], 'desc' : {}}))
    
    class RedirectLogger:
        def __init__(self, logger): self.logger = logger
        def write(self, msg):
            if msg == '\n': pass
            else: self.logger.info(msg)
        def flush(self): pass
    
    __ENV__.LOG = Logger('pygics')
    file_handler = TimedRotatingFileHandler(__ENV__.DIR._LOG_FILE_, when='D', backupCount=7)
    file_handler.setFormatter(Formatter('[%(asctime)s] %(message)s'))
    __ENV__.LOG.addHandler(file_handler)
    __ENV__.LOG.addHandler(StreamHandler())
    sys.stdout = RedirectLogger(__ENV__.LOG)
    
    setGlobals(ENV=__ENV__, PWD=__ENV__.PWD, PMD=__ENV__.PMD, LOG=__ENV__.LOG)

def server(ip, port=80, *modules):
     
    #===========================================================================
    # Initial Setup
    #===========================================================================
    environment(os.path.split(os.path.abspath(inspect.getmodule(inspect.stack()[1][0]).__file__))[0])
    __ENV__.NET.IP = ip
    __ENV__.NET.PORT = port
     
    #===========================================================================
    # Load Modules
    #===========================================================================
    
    try:
        for path in modules: ENV.MOD.install(path)
        for path in ENV.MOD.getRegistered()['list']: ENV.MOD.install(path)
    except Exception as e:
        LOG.exception(str(e))
        exit(1)
             
    #===========================================================================
    # Run Server
    #===========================================================================
    def __pygics_wsgi_application__(request, response):
        try: request = Request(request)
        except Response.__HTTP__ as e:
            LOG.exception(str(e))
            response(e.status, e.headers)
            return [e.data]
        except Exception as e:
            LOG.exception(str(e))
            response('400 Bad Request', [('Content-Type', ContentType.AppJson)])
            return [json.dumps({'error' : str(e)})]
        result = request.api(request, response)
        if isinstance(result, str): return [result.encode()]
        else: return [result]
    
    try:
        WSGIServer((ip, port),
                   application=__pygics_wsgi_application__,
                   log=LOG,
                   error_log=LOG).serve_forever()
    except (KeyboardInterrupt, SystemExit): print('pygics interrupted')
    except: raise
 
def export(method, url, content_type=ContentType.AppStream):
    
    def wrapper(logic):
        
        def exporter(req, res):
            try:
                # Run API Processing
                data = logic(req, *req.args, **req.kargs)
                # Deciding Content Type
                if isinstance(data, dict) or isinstance(data, list):
                    data = json.dumps(data)
                    content_type = req.content_type if req.content_type else ContentType.AppJson
                elif isinstance(data, str):
                    data = data
                    content_type = req.content_type if req.content_type else ContentType.TextPlain
                elif isinstance(data, int) or isinstance(data, float):
                    data = str(data)
                    content_type = req.content_type if req.content_type else ContentType.TextPlain
                elif isinstance(data, io.IOBase):
                    fd = data
                    content_type = req.content_type if req.content_type else ContentType.getType(fd.name)
                    data = fd.read()
                    fd.close()
                elif not data:
                    data = ''
                    content_type = req.content_type if req.content_type else ContentType.TextPlain
                else:
                    content_type = req.content_type if req.content_type else ContentType.AppStream
            # Exception Processing
            except Response.__HTTP__ as e:
                res(e.status, e.headers)
                return e.data
            except TypeError as e:
                LOG.exception(str(e))
                res('400 Bad Request', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            except Exception as e:
                LOG.exception(str(e))
                res('500 Internal Server Error', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            # Build Response
            headers = [('Content-Type', content_type)]
            if req.cookies_new:
                for k, v in req.cookies_new.items(): headers.append(('Set-Cookie', '%s=%s' % (k, v)))
            res('200 OK', headers)
            return data
        
        ENV.URI.register(logic, exporter, method, url, content_type)
        return exporter
     
    return wrapper

def plugin(plugin_instance):
    def wrapper(logic):
        def exporter(req, res):
            plugin_instance.__prev__(req, res)
            data = logic(req, res)
            return plugin_instance.__post__(req, res, data)
        if hasattr(logic, '__logic__'): exporter.__logic__ = logic.__logic__
        else: exporter.__logic__ = logic
        return exporter
    return wrapper

def rest(method, url):
    return export(method, url, content_type=ContentType.AppJson)
