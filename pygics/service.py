# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 29.
@author: HyechurnJang
'''

import os
import re
import sys
import time
import json
import uuid
import types
import shutil
import urllib
import zipfile
import inspect
import requests
import platform
import logging
import logging.handlers
from jzlib import modup, moddown
from mimetypes import MimeTypes
from gevent.pywsgi import WSGIServer
from .task import Burst

class ENV:
    
    UUID = None
    API = {}
     
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
        
        class __PygicsModuleLogRedirect__:
            def __init__(self, logger): self.logger = logger
            def write(self, msg):
                if msg == '\n': pass
                else: self.logger.info(msg)
        
        sys.stdout = __PygicsModuleLogRedirect__(cls.LOG.MODULE)
        
        print('PYGICS-UUID : %s' % cls.UUID)
        
        __builtins__['ENV'] = ENV
        __builtins__['pwd'] = ENV.pwd
        __builtins__['pmd'] = ENV.pmd
    
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
        ref = ENV.API
        for rn in rns:
            if rn in ref: ref = ref[rn]
            elif '__methods__' in ref and self.method in ref['__methods__']: break
            else: raise Response.NotFound()
        if '__methods__' not in ref: raise Response.NotFound()
        self.api = ref['__methods__'][self.method]
        self.url = ref['__api_url__']
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

#===============================================================================
# Internal Module Management
#===============================================================================
def __remove_module_file__(name):
    mod_path = '%s/%s' % (ENV.DIR.MOD, name)
    if os.path.exists(mod_path) and os.path.isdir(mod_path):
        shutil.rmtree(mod_path)
        return True
    return False

def __unlink_module__(name):
    if name in ENV.API:
        ENV.API.pop(name)
        ENV.LOG.MODULE.info('delete api /%s/*' % name)
    moddown(name)

def __link_module__(path):
    modup(path)

def __install_dependency__(path):
    path = path + '/dependency.txt'
    if os.path.exists(path):
        with open(path) as fd: modules = fd.readlines()
        span = []
        for module in modules:
            rq = re.match('\s*(?P<module>[\w\.\-\:]+)', module)
            if rq != None: span.append(rq.group('module'))
        modules = span
        for module in modules: __install_module__(module)
        return modules
    return []
    
def __uninstall_module__(name):
    if name not in ENV.MOD.PRIO: raise Exception('could not find module %s' % name)
    __unlink_module__(name)
    ENV.MOD.PRIO.remove(name)
    if name in ENV.MOD.DESC: ENV.MOD.DESC.pop(name)
    ENV.MOD.save()
    __remove_module_file__(name)

def __install_module__(path):
    if re.search('^sys::', path):
        os_desc = path.split('::')
        os_type = os_desc[1].lower()
        os_dist = os_desc[2] if len(os_desc) > 2 else None
        os_ver = os_desc[3] if len(os_desc) > 3 else None
        if os_type != ENV.SYS.OS: raise Exception('could not support operation system')
        elif os_dist != None and os_dist != ENV.SYS.DIST: raise Exception('could not support operation system')
        elif os_ver != None and os_ver != ENV.SYS.VER: raise Exception('could not support operation system')
        print('system %s is matched' % path)
    elif re.search('^pkg::', path):
        package = path.replace('pkg::', '')
        if ENV.SYS.DIST in ['centos', 'redhat', 'fedora']: syscmd = 'yum install -q -y %s'
        elif ENV.SYS.DIST in ['ubuntu', 'debian']: syscmd = 'apt-get install -q -y %s'
        else: raise Exception('could not support installing system package')
        if os.system(syscmd % package) != 0: raise Exception('could not install system package %s' % path)
        print('system package %s is installed' % path)
    elif re.search('^pip::', path):
        if os.system('pip install -q %s' % path.replace('pip::', '')) != 0: raise Exception('could not install %s' % path)
        print('package %s is installed' % path)
    elif re.search('^app::', path) or re.search('^exp::', path):
        repo_desc = path.split('::')
        repo = repo_desc[0]
        name = repo_desc[1]
        branch = repo_desc[2] if len(repo_desc) > 2 else 'master'
        if name in ENV.MOD.PRIO: return
        mod_path = '%s/%s' % (ENV.DIR.MOD, name)
        if os.path.exists(mod_path) and os.path.isdir(mod_path):
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
        else:
            gzip_path = '%s.zip' % mod_path
            uzip_path = '%s/%s-%s' % (mod_path, name, branch)
            move_path = '%s/%s-%s' % (ENV.DIR.MOD, name, branch)
            if repo == 'app': resp = requests.get('https://github.com/pygics-app/%s/archive/%s.zip' % (name, branch))
            elif repo == 'exp': resp = requests.get('https://github.com/pygics-app-exp/%s/archive/%s.zip' % (name, branch))
            else: raise Exception('incorrect repository name %s' % repo)
            if resp.status_code != 200: raise Exception('could not find %s' % path)
            with open(gzip_path, 'wb') as fd: fd.write(resp.content)
            with zipfile.ZipFile(gzip_path, 'r') as fd: fd.extractall(mod_path)
            os.remove(gzip_path)
            shutil.move(uzip_path, ENV.DIR.MOD)
            shutil.rmtree(mod_path)
            os.rename(move_path, mod_path)
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
        ENV.MOD.DESC[name] = {'path' : path, 'base' : repo, 'name' : name, 'dist' : branch, 'deps' : deps, 'time' : time.strftime('%Y-%m-%d %X', time.localtime())}
        ENV.MOD.PRIO.append(name)
        ENV.MOD.save()
        print('module %s is installed' % path)
    else:
        if not os.path.exists(path): raise Exception('incorrect module path %s' % path)
        parent, name = os.path.split(path)
        name, ext = os.path.splitext(name)
        if zipfile.is_zipfile(path):
            mod_path = '%s/%s' % (ENV.DIR.MOD, name)
            if name in ENV.MOD.PRIO: __unlink_module__(name)
            __remove_module_file__(name)
            with zipfile.ZipFile(path, 'r') as fd: fd.extractall(mod_path)
            os.remove(path)
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
            path = mod_path
        elif os.path.isdir(path):
            if name in ENV.MOD.PRIO: return
            deps = __install_dependency__(path)
            __link_module__(path)
        elif os.path.isfile(path):
            if ext == '.py':
                if name in ENV.MOD.PRIO: return
                deps = []
                __link_module__('%s/%s' % (parent, name))
            elif ext == '.raw':
                mod_path = '%s/%s' % (ENV.DIR.MOD, name)
                mod_init = '%s/__init__.py' % mod_path
                deps = []
                if name in ENV.MOD.PRIO: __unlink_module__(name)
                __remove_module_file__(name)
                os.mkdir(mod_path)
                shutil.move(path, mod_init)
                __link_module__(mod_path)
                path = mod_path
            else: raise Exception('could not install %s' % path)
        else: raise Exception('could not install %s' % path)
        if name not in ENV.MOD.PRIO: ENV.MOD.PRIO.append(name)
        ENV.MOD.DESC[name] = {'path' : path, 'base' : 'local module', 'name' : name, 'dist' : None, 'deps' : deps, 'time' : time.strftime('%Y-%m-%d %X', time.localtime())}
        ENV.MOD.save()
        print('module %s is installed' % path)

def api(method, url, content_type=None, **plugins):
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
        ref = ENV.API
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        if '__methods__' not in ref: ref['__methods__'] = {}
        ref['__methods__'][method_upper] = decofunc
        ref['__api_url__'] = dn
        ref['__content_type__'] = content_type
        print('register api <%s:%s> link to <%s.%s>' % (method_upper, dn, module_name, func_name))
        return decofunc
    
    return api_wrapper

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
    @api('GET', 'module')
    def get_module(req):
        return {'prio' : ENV.MOD.PRIO, 'desc' : ENV.MOD.DESC}
    
    @api('POST', 'module')
    def upload_module(req, name):
        if 'PYGICS_UUID' not in req.headers or req.headers['PYGICS_UUID'] != ENV.UUID: raise Exception('incorrect uuid')
        raw_file = '%s/%s.raw' % (ENV.DIR.MOD, name)
        with open(raw_file, 'wb') as fd: fd.write(req.data)
        __install_module__(raw_file)
        return {'result': 'success'}
            
    @api('DELETE', 'module')
    def delete_module(req, name):
        if 'PYGICS_UUID' not in req.headers or req.headers['PYGICS_UUID'] != ENV.UUID: raise Exception('incorrect uuid')
        __uninstall_module__(name)
        return {'result': 'success'}
    
    @api('GET', 'repo')
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
    
    @api('POST', 'repo')
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
    