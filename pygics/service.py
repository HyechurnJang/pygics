# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 29.
@author: HyechurnJang
'''

import os
import re
import sys
import json
import uuid
import shutil
import zipfile
import inspect
import requests
import platform
import logging
import logging.handlers
from gevent.pywsgi import WSGIServer
from .core import __PYGICS__
from .task import Task, Burst

class __PygicsServiceEnvironment__:
    
    class __PygicsServiceDirectory__:
        ROOT = os.path.expanduser('~') + '/.pygics'
        SVC = None
        MOD = None
        RSC = None
    
    class __PygicsServiceNetwork__:
        IP = None
        PORT = None
        
    class __PygicsServiceManagement__:
        UUID = None
        PLOG = None
        MLOG = None
    
    class __PygicsServiceSystem__:
        OS = None
        DIST = None
        VER = None
    
    class __PygicsServiceModule__:
        STATIC = []
        UPLOAD = []
        
    DIR = __PygicsServiceDirectory__
    NET = __PygicsServiceNetwork__
    MNG = __PygicsServiceManagement__
    SYS = __PygicsServiceSystem__
    MOD = __PygicsServiceModule__
    API = {'GET' : {}, 'POST' : {}, 'PUT' : {}, 'DELETE' : {}}
    
    @classmethod
    def __environment_init__(cls):
        if 'PYGICS' not in __builtins__:
            __builtins__['PYGICS'] = __PygicsServiceEnvironment__
        if 'PWD' not in __builtins__:
            __builtins__['PWD'] = __PygicsServiceEnvironment__.__module_pwd__
    
    @classmethod
    def __module_pwd__(cls):
        mod = inspect.getmodule(inspect.stack()[1][0])
        mod_path, _ = os.path.split(mod.__file__)
        return mod_path
            
    @classmethod    
    def __service_init__(cls, ip, port, clean_init):
        cls.NET.IP = ip
        cls.NET.PORT = port
        cls.DIR.SVC = cls.DIR.ROOT + '/%s_%s' % (ip, str(str(port)))
        cls.DIR.MOD = cls.DIR.SVC + '/modules'
        if not os.path.exists(cls.DIR.ROOT): os.mkdir(cls.DIR.ROOT)
        if clean_init: shutil.rmtree(cls.DIR.SVC)
        if not os.path.exists(cls.DIR.SVC): os.mkdir(cls.DIR.SVC)
        if not os.path.exists(cls.DIR.MOD): os.mkdir(cls.DIR.MOD)
        l_os, l_ver, _ = platform.dist()
        w_os, w_ver, _, _ = platform.win32_ver()
        if l_os != '':
            cls.SYS.OS = 'linux'
            cls.SYS.DIST = l_os.lower()
            cls.SYS.VER = l_ver
        elif w_os != '':
            cls.SYS.OS = 'windows'
            cls.SYS.DIST = w_os.lower()
            cls.SYS.VER = w_ver
        else:
            cls.SYS.OS = 'unknown'
            cls.SYS.VER = 'unknown'
        if os.path.exists(cls.DIR.SVC + '/service.uuid'):
            with open(cls.DIR.SVC + '/service.uuid') as fd: cls.MNG.UUID = fd.read()
        else:
            cls.MNG.UUID = str(uuid.uuid4()).replace('-', '')
            with open(cls.DIR.SVC + '/service.uuid', 'w') as fd: fd.write(cls.MNG.UUID)
        if not os.path.exists(cls.DIR.SVC + '/modules.dep'):
            with open(cls.DIR.SVC + '/modules.dep', 'w') as fd: fd.write('[]')
        cls.MNG.PLOG = logging.Logger('pygics')
        cls.MNG.MLOG = logging.Logger('pygics-module')
        log_scrn = logging.StreamHandler()
        plog_file = logging.handlers.TimedRotatingFileHandler(cls.DIR.SVC + '/pygics.log', when='D', backupCount=7)
        mlog_file = logging.handlers.TimedRotatingFileHandler(cls.DIR.SVC + '/modules.log', when='D', backupCount=7)
        mlog_file.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        cls.MNG.PLOG.addHandler(log_scrn)
        cls.MNG.PLOG.addHandler(plog_file)
        cls.MNG.MLOG.addHandler(log_scrn)
        cls.MNG.MLOG.addHandler(mlog_file)
        
        class __PygicsServiceModuleLogRedirect__:
            def __init__(self, logger): self.logger = logger
            def write(self, msg):
                if msg == '\n': pass
                else: self.logger.info(msg)
        
        sys.stdout = __PygicsServiceModuleLogRedirect__(cls.MNG.MLOG)

class ContentType:
    
    AppJson = 'application/json'
    AppJS = 'application/javascript'
    AppStream = 'application/octet-stream'
    TextPlain = 'text/plain'
    TextHtml = 'text/html'
    TextCss = 'text/css'

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
        self.kargs = {}
        qs = req['QUERY_STRING'].split('&')
        for q in qs:
            kv = re.match('(?P<key>\w+)=("|%22|%27)?(?P<val>[\w\.\-\:]+)("|%22|%27)?', q)
            if kv: self.kargs[kv.group('key')] = kv.group('val')
        if self.method in ['POST', 'PUT']:
            raw_data = req['wsgi.input'].read()
            if 'CONTENT_TYPE' in req: content_type = req['CONTENT_TYPE']
            else: content_type = ContentType.TextPlain
            if ContentType.AppJson in content_type: self.data = json.loads(raw_data)
            else: self.data = raw_data
        else: self.data = None
        rns = filter(None, self.path.split('/'))
        rns_len = len(rns)
        ref = PYGICS.API[self.method]
        for i in range(0, rns_len):
            rn = rns[i]
            if rn in ref: ref = ref[rns[i]]
            elif '__api_ref__' in ref: break
            else: raise Request.NotFound()
        self.api = ref['__api_ref__']
        self.url = ref['__api_url__']
        self.args = filter(None, re.sub(self.url, '', self.path, 1).split('/'))
        
    def __str__(self):
        return '%s : %s\nHeader : %s\nArgs : %s\nQuery : %s\nData : %s' % (self.method, self.url, self.header, self.args, self.kargs, self.data)

def api(method, url, content_type=ContentType.AppJson, url_absolute=False):
    def api_wrapper(func):
        def decofunc(req, res):
            try: ret = func(req, *req.args, **req.kargs)
            except TypeError as e:
                PYGICS.MNG.MLOG.exception(str(e))
                res('400 Bad Request', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            except Exception as e:
                PYGICS.MNG.MLOG.exception(str(e))
                res('500 Internal Server Error', [('Content-Type', ContentType.AppJson)])
                return json.dumps({'error' : str(e)})
            if content_type == ContentType.AppJson:
                res('200 OK', [('Content-Type', content_type)])
                return json.dumps({'result' : ret})
            res('200 OK', [('Content-Type', content_type)])
            return ret
        
        __PygicsServiceEnvironment__.__environment_init__()
        
        if url[0] != '/': furl = '/' + url
        else: furl = url
        if url_absolute: dn = furl
        else:
            module_name = func.__module__
            func_name = func.__name__
            if module_name == '__main__': dn = furl
            elif module_name == 'pygics.service': dn = '/pygics%s' % furl 
            else: dn = '/%s%s' % (module_name, furl)
        rns = filter(None, dn.split('/'))
        ref = PYGICS.API[method.upper()]
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        ref['__api_url__'] = dn
        ref['__api_ref__'] = decofunc
        if url_absolute: print('register api <%s:%s> by absolute path, result-type=%s' % (method.upper(), dn, content_type))
        else: print('register api <%s:%s> link to <%s.%s>, result-type=%s' % (method.upper(), dn, module_name, func_name, content_type))
        
        return decofunc
    return api_wrapper


def __save_module_dep__():
    with open(PYGICS.DIR.SVC + '/modules.dep', 'w') as fd: fd.write(json.dumps(PYGICS.MOD.UPLOAD))

def __remove_module_file__(name):
    py_path = '%s/%s.py' % (PYGICS.DIR.MOD, name)
    pyc_path = '%s/%s.pyc' % (PYGICS.DIR.MOD, name)
    pack_path = '%s/%s' % (PYGICS.DIR.MOD, name)
    if os.path.exists(pack_path) and os.path.isdir(pack_path): shutil.rmtree(pack_path)
    elif os.path.exists(py_path) and os.path.isfile(py_path):
        os.remove(py_path)
        if os.path.exists(pyc_path) and os.path.isfile(pyc_path):
            os.remove(pyc_path)

def __unlink_module__(name):
    if name in PYGICS.API['GET']:
        PYGICS.API['GET'].pop(name)
        PYGICS.MNG.MLOG.info('delete api <GET:/%s/*>' % name)
    if name in PYGICS.API['POST']:
        PYGICS.API['POST'].pop(name)
        PYGICS.MNG.MLOG.info('delete api <POST:/%s/*>' % name)
    if name in PYGICS.API['PUT']:
        PYGICS.API['PUT'].pop(name)
        PYGICS.MNG.MLOG.info('delete api <PUT:/%s/*>' % name)
    if name in PYGICS.API['DELETE']:
        PYGICS.API['DELETE'].pop(name)
        PYGICS.MNG.MLOG.info('delete api <DELETE:/%s/*>' % name)
    if name in sys.modules:
        mod = sys.modules.pop(name)
        for _, val in mod.__dict__.items():
            if isinstance(val, __PYGICS__): val.__pygics_inspect_release__()
        del mod

def __link_module__(path, name):
    if path != '' and path not in sys.path: sys.path.insert(0, path)
    __import__(name)

def __install_requirements__(path, static=False):
    if os.path.exists(path):
        with open(path) as fd: packages = fd.readlines()
        span = []
        for path in packages:
            rq = re.match('\s*(?P<package>[\w\.\-\:]+)', path)
            if rq != None: span.append(rq.group('package'))
        packages = span
        for path in packages: install_module(path, static)
    
def uninstall_module(name):
    if name in PYGICS.MOD.STATIC: raise Exception('could not uninstall static module %s' % name)
    if name not in PYGICS.MOD.UPLOAD: raise Exception('could not find module %s' % name)
    __unlink_module__(name)
    PYGICS.MOD.UPLOAD.remove(name)
    __save_module_dep__()
    __remove_module_file__(name)

def install_module(path, static=False):
    if '::' in path:
        cmd = path[:5]
        if 'sys::' == cmd:
            os_desc = path.split('::')
            os_type = os_desc[1].lower()
            os_dist = os_desc[2] if len(os_desc) > 2 else None
            os_ver = os_desc[3] if len(os_desc) > 3 else None
            if os_type != PYGICS.SYS.OS: raise Exception('could not support operation system')
            elif os_dist != None and os_dist != PYGICS.SYS.DIST: raise Exception('could not support operation system')
            elif os_ver != None and os_ver != PYGICS.SYS.VER: raise Exception('could not support operation system')
            print('system %s is matched' % path)
            return
        elif 'pkg::' == cmd:
            package = path.replace('pkg::', '')
            if PYGICS.SYS.DIST in ['centos', 'redhat', 'fedora']: syscmd = 'yum install -q -y %s'
            elif PYGICS.SYS.DIST in ['ubuntu', 'debian']: syscmd = 'apt-get install -q -y %s'
            else: raise Exception('could not support installing system package')
            if os.system(syscmd % package) != 0: raise Exception('could not install system package %s' % path)
            print('system package %s is installed' % path)
            return
        elif 'pip::' == cmd:
            if os.system('pip install -q %s' % path.replace('pip::', '')) != 0: raise Exception('could not install %s' % path)
            print('package %s is installed' % path)
            return
        elif 'app::' == cmd or 'exp::' == cmd:
            repo_desc = path.split('::')
            repo = repo_desc[0]
            name = repo_desc[1]
            branch = repo_desc[2] if len(repo_desc) == 3 else 'master'
            if name in PYGICS.MOD.STATIC: return
            if name in PYGICS.MOD.UPLOAD: return
            mod_path = '%s/%s' % (PYGICS.DIR.MOD, name)
            if os.path.exists(mod_path) and os.path.isdir(mod_path):
                install_module(mod_path, static)
                return
            gzip_path = '%s.zip' % mod_path
            uzip_path = '%s/%s-%s' % (mod_path, name, branch)
            move_path = '%s/%s-%s' % (PYGICS.DIR.MOD, name, branch)
            if repo == 'app': resp = requests.get('https://github.com/pygics-app/%s/archive/%s.zip' % (name, branch))
            else: resp = requests.get('https://github.com/pygics-app-exp/%s/archive/%s.zip' % (name, branch))
            if resp.status_code != 200: raise Exception('could not find %s' % path)
            with open(gzip_path, 'wb') as fd: fd.write(resp.content)
            with zipfile.ZipFile(gzip_path, 'r') as fd: fd.extractall(mod_path)
            os.remove(gzip_path)
            shutil.move(uzip_path, PYGICS.DIR.MOD)
            shutil.rmtree(mod_path)
            os.rename(move_path, mod_path)
            __install_requirements__(mod_path + '/requirements.txt', static)
            __link_module__(PYGICS.DIR.MOD, name)
            if static: PYGICS.MOD.STATIC.append(name)
            elif name not in PYGICS.MOD.UPLOAD:
                PYGICS.MOD.UPLOAD.append(name)
                __save_module_dep__()
            print('module %s is installed' % path)
            return
    else:
        parent, name = os.path.split(path)
        name, ext = os.path.splitext(name)
        if ext == '.raw':
            if zipfile.is_zipfile(path):
                if name in PYGICS.MOD.STATIC: raise Exception('could not reinstall static module %s' % name)
                mod_path = '%s/%s' % (PYGICS.DIR.MOD, name)
                if name in PYGICS.MOD.UPLOAD: __unlink_module__(name)
                __remove_module_file__(name)
                with zipfile.ZipFile(path, 'r') as fd: fd.extractall(mod_path)
                os.remove(path)
                __install_requirements__(mod_path + '/requirements.txt', static)
                __link_module__(PYGICS.DIR.MOD, name)
                if static: PYGICS.MOD.STATIC.append(name)
                elif name not in PYGICS.MOD.UPLOAD:
                    PYGICS.MOD.UPLOAD.append(name)
                    __save_module_dep__()
            else:
                if name in PYGICS.MOD.STATIC: raise Exception('could not reinstall static module %s' % name)
                if name in PYGICS.MOD.UPLOAD: __unlink_module__(name)
                __remove_module_file__(name)
                os.rename(path, '%s/%s.py' % (parent, name))
                __link_module__(PYGICS.DIR.MOD, name)
                if static: PYGICS.MOD.STATIC.append(name)
                elif name not in PYGICS.MOD.UPLOAD:
                    PYGICS.MOD.UPLOAD.append(name)
                    __save_module_dep__()
        elif ext == '':
            if name in PYGICS.MOD.STATIC: raise Exception('could not reinstall static module %s' % name)
            elif name in PYGICS.MOD.UPLOAD: return
            __install_requirements__(path + '/requirements.txt', static)
            __link_module__(parent, name)
            if static: PYGICS.MOD.STATIC.append(name)
            elif name not in PYGICS.MOD.UPLOAD:
                PYGICS.MOD.UPLOAD.append(name)
                __save_module_dep__()
        elif ext == '.py':
            if name in PYGICS.MOD.STATIC: raise Exception('could not reinstall static module %s' % name)
            elif name in PYGICS.MOD.UPLOAD: return
            __link_module__(parent, name)
            if static: PYGICS.MOD.STATIC.append(name)
            elif name not in PYGICS.MOD.UPLOAD:
                PYGICS.MOD.UPLOAD.append(name)
                __save_module_dep__()
        else: raise Exception('could not install %s' % path)
        print('module %s is installed' % path)
        return
    raise Exception('%s is incorrect requirement' % path)

def server(ip,
           port=80,
           modules=[],
           resource={},
           clean_init=False):
    
    #===========================================================================
    # Initial Setup
    #===========================================================================
    __PygicsServiceEnvironment__.__environment_init__()
    PYGICS.__service_init__(ip, port, clean_init)
    PYGICS.DIR.RSC = resource['root'] if 'root' in resource else './'
    resource_read = resource['read'] if 'read' in resource else False
    resource_write = resource['write'] if 'write' in resource else False
    
    #===========================================================================
    # Define Built-in Functions
    #===========================================================================
    def __pygics_wsgi_application__(req, res):
        try: req = Request(req)
        except Request.NotFound as e:
            PYGICS.MNG.MLOG.exception(str(e))
            res('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({'error' : str(e)})]
        except Exception as e:
            PYGICS.MNG.MLOG.exception(str(e))
            res('400 Bad Request', [('Content-Type', 'application/json')])
            return [json.dumps({'error' : str(e)})]
        return [req.api(req, res)]

    #===========================================================================
    # Management Admin Rest APIs
    #===========================================================================
    @api('GET', '/module')
    def get_module(req):
        return {'static' : PYGICS.MOD.STATIC, 'upload' : PYGICS.MOD.UPLOAD}
    
    @api('POST', '/module')
    def upload_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        raw_file = '%s/%s.raw' % (PYGICS.DIR.MOD, name)
        with open(raw_file, 'wb') as fd: fd.write(req.data)
        install_module(raw_file)
        return 'success'
            
    @api('DELETE', '/module')
    def delete_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        uninstall_module(name)
        return 'success'
    
    @api('GET', '/repo')
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
    
    @api('POST', '/repo')
    def install_repo(req, repo, name, branch='master'):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        if repo not in ['app', 'exp']: raise Exception('incorrect repository name')
        install_module('%s::%s::%s' % (repo, name, branch))
        return 'success'
    
    @api('GET', '/resource', content_type='application/octet-stream')
    def download_resource(req, *argv):
        if PYGICS.DIR.RSC == None or resource_read == False: raise Exception('not permitted')
        rel_path = '/'.join(argv)
        if rel_path == '': raise Exception('incorrect resource path')
        path = '%s/%s' % (PYGICS.DIR.RSC, rel_path)
        if not os.path.exists(path) or not os.path.isfile(path): raise Exception('could not find object')
        with open(path, 'rb') as fd:
            return fd.read()
    
    @api('POST', '/resource')
    def upload_resource(req, *argv):
        if PYGICS.DIR.RSC == None or resource_write == False: raise Exception('not permitted')
        rel_path = '/'.join(argv)
        if rel_path == '': raise Exception('incorrect resource path')
        path = '%s/%s' % (PYGICS.DIR.RSC, rel_path)
        parents, _ = os.path.split(path)
        if not os.path.exists(parents): raise Exception('could not find directory')
        with open(path, 'wb') as fd:
            fd.write(req.data)
        return True
    
    @api('DELETE', '/resource')
    def delete_resource(req, *argv):
        if PYGICS.DIR.RSC == None or resource_write == False: raise Exception('not permitted')
        rel_path = '/'.join(argv)
        if rel_path == '': raise Exception('incorrect resource path')
        path = '%s/%s' % (PYGICS.DIR.RSC, rel_path)
        if not os.path.exists(path) and not os.path.isfile(path): raise Exception('could not find object')
        os.remove(path)
        return True
        
    print('module pygics is installed')
    
    #===========================================================================
    # Load Modules
    #===========================================================================
    for module in modules: install_module(module, static=True)
    try:
        with open(PYGICS.DIR.SVC + '/modules.dep', 'r') as fd: upload_modules = json.loads(fd.read())
    except Exception as e:
        PYGICS.MNG.MLOG.exception(str(e))
    else:
        for module in upload_modules:
            file_path = '%s/%s.py' % (PYGICS.DIR.MOD, module)
            pack_path = '%s/%s' % (PYGICS.DIR.MOD, module)
            if os.path.isfile(file_path): install_module(file_path)
            elif os.path.isdir(pack_path): install_module(pack_path)
    
    #===========================================================================
    # Run Server
    #===========================================================================
    WSGIServer((ip, port),
               application=__pygics_wsgi_application__,
               log=PYGICS.MNG.PLOG,
               error_log=PYGICS.MNG.PLOG).serve_forever()
    