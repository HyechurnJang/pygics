# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 29.
@author: HyechurnJang
'''

import os
import re
import sys
import pip
import json
import uuid
import shutil
import zipfile
import requests
import logging
import logging.handlers
from gevent.pywsgi import WSGIServer
from .task import Task

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
    
    class __PygicsServiceModule__:
        STATIC = []
        UPLOAD = []
        
    DIR = __PygicsServiceDirectory__
    NET = __PygicsServiceNetwork__
    MNG = __PygicsServiceManagement__
    MOD = __PygicsServiceModule__
    REST = {'GET' : {}, 'POST' : {}, 'PUT' : {}, 'DELETE' : {}}
    
    @classmethod
    def __environment_init__(cls):
        if 'PYGICS' not in __builtins__:
            __builtins__['PYGICS'] = __PygicsServiceEnvironment__
            
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
        if os.path.exists(cls.DIR.SVC + '/service.uuid'):
            with open(cls.DIR.SVC + '/service.uuid') as fd: cls.MNG.UUID = fd.read()
        else:
            cls.MNG.UUID = str(uuid.uuid4()).replace('-', '')
            with open(cls.DIR.SVC + '/service.uuid', 'w') as fd: fd.write(cls.MNG.UUID)
        if not os.path.exists(cls.DIR.SVC + '/modules.prio'):
            with open(cls.DIR.SVC + '/modules.prio', 'w') as fd: fd.write('[]')
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
            kv = re.match('(?P<key>\w+)=("|%22|%27)?(?P<val>[\w-]+)("|%22|%27)?', q)
            if kv: self.kwargs[kv.group('key')] = kv.group('val')
        if self.method in ['POST', 'PUT']:
            raw_data = req['wsgi.input'].read()
            if 'CONTENT_TYPE' in req: content_type = req['CONTENT_TYPE']
            else: content_type = 'text/plain'
            if 'application/json' in content_type: self.data = json.loads(raw_data)
            elif 'text/plain' in content_type: self.data = raw_data
            else: raise Request.UnsupportContentType()
        else: self.data = None
        rns = filter(None, self.path.split('/'))
        rns_len = len(rns)
        ref = PYGICS.REST[self.method]
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

def api(method, url, content_type='application/json'):
    def api_wrapper(func):
        def decofunc(req, res):
            try: ret = func(req, *req.args, **req.kwargs)
            except TypeError as e:
                PYGICS.MNG.MLOG.exception(str(e))
                res('400 Bad Request', [('Content-Type', 'application/json')])
                return json.dumps({'error' : str(e)})
            except Exception as e:
                PYGICS.MNG.MLOG.exception(str(e))
                res('500 Internal Server Error', [('Content-Type', 'application/json')])
                return json.dumps({'error' : str(e)})
            if content_type == 'application/json':
                res('200 OK', [('Content-Type', 'application/json')])
                return json.dumps({'result' : ret})
            res('200 OK', [('Content-Type', content_type)])
            return ret
        
        __PygicsServiceEnvironment__.__environment_init__()
        
        #=======================================================================
        # get names & url
        #=======================================================================
        module_name = func.__module__
        func_name = func.__name__
        if url[0] != '/': furl = '/' + url
        else: furl = url
        
        #=======================================================================
        # get dn
        #=======================================================================
        if module_name == '__main__': dn = furl
        elif module_name == 'pygics.service': dn = '/pygics%s' % furl 
        else: dn = '/%s%s' % (module_name, furl)
        
        #=======================================================================
        # get rns
        #=======================================================================
        rns = filter(None, dn.split('/'))
        
        #=======================================================================
        # register
        #=======================================================================
        ref = PYGICS.REST[method.upper()]
        for rn in rns:
            if rn not in ref: ref[rn] = {}
            ref = ref[rn]
        ref['__api_url__'] = dn
        ref['__api_ref__'] = decofunc
        print('register api <%s:%s> link to <%s.%s>' % (method.upper(), dn, module_name, func_name))
        
        return decofunc
    return api_wrapper

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
    PYGICS.DIR.RSC = resource['root'] if 'root' in resource else None
    resource_read = resource['read'] if 'read' in resource else True
    resource_write = resource['write'] if 'write' in resource else False
    
    #===========================================================================
    # Define Built-in Functions
    #===========================================================================
    def __pygics_wsgi_application__(req, res):
        try: req = Request(req)
        except Request.NotFound as e:
            PYGICS.MNG.MLOG.exception(str(e))
            res('404 Not Found', [('Content-Type', 'application/json')])
            return json.dumps({'error' : str(e)})
        except Exception as e:
            PYGICS.MNG.MLOG.exception(str(e))
            res('400 Bad Request', [('Content-Type', 'application/json')])
            return json.dumps({'error' : str(e)})
        try: return [req.api(req, res)]
        except Exception as e:
            PYGICS.MNG.MLOG.exception(str(e))
            res('500 Internal Server Error', [('Content-Type', 'application/json')])
            return json.dumps({'error' : str(e)})
        
    def __delete_module_without_name__(mod_name):
        if mod_name in PYGICS.REST['GET']:
            PYGICS.REST['GET'].pop(mod_name)
            PYGICS.MNG.MLOG.info('delete api <GET:/%s/*>' % mod_name)
        if mod_name in PYGICS.REST['POST']:
            PYGICS.REST['POST'].pop(mod_name)
            PYGICS.MNG.MLOG.info('delete api <POST:/%s/*>' % mod_name)
        if mod_name in PYGICS.REST['PUT']:
            PYGICS.REST['PUT'].pop(mod_name)
            PYGICS.MNG.MLOG.info('delete api <PUT:/%s/*>' % mod_name)
        if mod_name in PYGICS.REST['DELETE']:
            PYGICS.REST['DELETE'].pop(mod_name)
            PYGICS.MNG.MLOG.info('delete api <DELETE:/%s/*>' % mod_name)
        if mod_name in sys.modules:
            module = sys.modules.pop(mod_name)
            for _, val in module.__dict__.items():
                if isinstance(val, Task): val.stop()
            del module
    
    def __delete_module__(mod_name):
        if mod_name in PYGICS.MOD.UPLOAD:
            __delete_module_without_name__(mod_name)
            PYGICS.MOD.UPLOAD.remove(mod_name)
            with open(PYGICS.DIR.SVC + '/modules.prio', 'w') as fd: fd.write(json.dumps(PYGICS.MOD.UPLOAD))
            return 'success'
        raise Exception('non-exist module')
    
    def __load_module__(path, static=False):
        if os.path.isfile(path):
            directory, file_name = os.path.split(path)
            mod_name, mod_ext = os.path.splitext(file_name)
            if mod_ext == '.py':
                if mod_name in PYGICS.MOD.STATIC:
                    raise Exception('could not upload with static module name')
                if mod_name in PYGICS.MOD.UPLOAD:
                    try: __delete_module_without_name__(mod_name)
                    except: pass
                if directory != '' and directory not in sys.path: sys.path.insert(0, directory)
                try: __import__(mod_name)
                except Exception as e:
                    if not static and mod_name in PYGICS.MOD.UPLOAD: PYGICS.MOD.UPLOAD.remove(mod_name)
                    PYGICS.MNG.MLOG.exception(str(e))
                    raise e
                if static: PYGICS.MOD.STATIC.append(mod_name)
                elif mod_name not in PYGICS.MOD.UPLOAD:
                    PYGICS.MOD.UPLOAD.append(mod_name)
                    with open(PYGICS.DIR.SVC + '/modules.prio', 'w') as fd: fd.write(json.dumps(PYGICS.MOD.UPLOAD))
                return 'success'
        elif os.path.isdir(path) and os.path.exists(path + '/__init__.py'):
            parents, pac_name = os.path.split(path)
            if pac_name in PYGICS.MOD.STATIC:
                raise Exception('could not upload with static module name')
            if pac_name in PYGICS.MOD.UPLOAD:
                try: __delete_module_without_name__(pac_name)
                except: pass
            __load_requirements__(path + '/requirements.txt')
            if path not in sys.path: sys.path.insert(0, parents)
            try: __import__(pac_name)
            except Exception as e:
                if not static and pac_name in PYGICS.MOD.UPLOAD: PYGICS.MOD.UPLOAD.remove(pac_name)
                PYGICS.MNG.MLOG.exception(str(e))
                raise e
            if static: PYGICS.MOD.STATIC.append(pac_name)
            elif pac_name not in PYGICS.MOD.UPLOAD:
                PYGICS.MOD.UPLOAD.append(pac_name)
                with open(PYGICS.DIR.SVC + '/modules.prio', 'w') as fd: fd.write(json.dumps(PYGICS.MOD.UPLOAD))
            return 'success'
        raise Exception('non-exist module')
    
    def __load_repo_module__(name, branch='master'):
        resp = requests.get('https://github.com/pygics-app/%s/archive/%s.zip' % (name, branch))
        if resp.status_code != 200: raise Exception('incorrect repo')
        pyg_file_path = PYGICS.DIR.MOD + '/' + name + '.pyg'
        package_path = PYGICS.DIR.MOD + '/' + name
        package_code_path = PYGICS.DIR.MOD + '/' + name + '/%s-%s' % (name, branch)
        package_code_move_path = PYGICS.DIR.MOD + '/%s-%s' % (name, branch) 
        code_path = PYGICS.DIR.MOD + '/' + name + '.py'
        compile_path = PYGICS.DIR.MOD + '/' + name + '.pyc'
        if os.path.exists(package_path) and os.path.isdir(package_path): shutil.rmtree(package_path)
        elif os.path.exists(code_path) and os.path.isfile(code_path):
            if os.path.exists(compile_path): os.remove(compile_path)
            os.remove(code_path)
        with open(pyg_file_path, 'wb') as fd: fd.write(resp.content)
        with zipfile.ZipFile(pyg_file_path, 'r') as zfd: zfd.extractall(package_path)
        os.remove(pyg_file_path)
        shutil.move(package_code_path, PYGICS.DIR.MOD)
        shutil.rmtree(package_path)
        os.rename(package_code_move_path, package_path)
        return __load_module__(package_path)
    
    def __load_pip_module__(name):
        if pip.main(['install', '-q', name]) == 0: return True
        return False
    
    def __load_requirements__(path):
        if not os.path.exists(path): return False
        with open(path) as fd: packages = fd.readlines()
        span = []
        for p in packages: span.append(re.match('(?P<package>[\w:]+)', p).group('package'))
        packages = span
        for p in packages:
            if 'pygics::' in p:
                rname = p.replace('pygics::', '')
                if rname in PYGICS.MOD.STATIC: continue
                if rname in PYGICS.MOD.UPLOAD: continue
                __load_repo_module__(rname)
            else: __load_pip_module__(p)
        return True
    
    #===========================================================================
    # Management Admin Rest APIs
    #===========================================================================
    @api('GET', '/module')
    def get_module(req):
        return {'static' : PYGICS.MOD.STATIC, 'upload' : PYGICS.MOD.UPLOAD}
    
    @api('POST', '/module')
    def load_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        pyg_file_path = PYGICS.DIR.MOD + '/' + name + '.pyg'
        package_path = PYGICS.DIR.MOD + '/' + name
        code_path = PYGICS.DIR.MOD + '/' + name + '.py'
        compile_path = PYGICS.DIR.MOD + '/' + name + '.pyc'
        if os.path.exists(package_path) and os.path.isdir(package_path): shutil.rmtree(package_path)
        elif os.path.exists(code_path) and os.path.isfile(code_path):
            if os.path.exists(compile_path): os.remove(compile_path)
            os.remove(code_path)
        with open(pyg_file_path, 'wb') as fd: fd.write(req.data)
        if zipfile.is_zipfile(pyg_file_path):
            with zipfile.ZipFile(pyg_file_path, 'r') as zfd: zfd.extractall(package_path)
            os.remove(pyg_file_path)
            return __load_module__(package_path)
        else:
            os.rename(pyg_file_path, code_path)
            return __load_module__(code_path)
    
    @api('DELETE', '/module')
    def del_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        ret = __delete_module__(name)
        package_path = PYGICS.DIR.MOD + '/' + name
        code_path = PYGICS.DIR.MOD + '/' + name + '.py'
        compile_path = PYGICS.DIR.MOD + '/' + name + '.pyc'
        if os.path.exists(package_path) and os.path.isdir(package_path): shutil.rmtree(package_path)
        elif os.path.exists(code_path) and os.path.isfile(code_path):
            if os.path.exists(compile_path): os.remove(compile_path)
            os.remove(code_path)
        return ret
    
    @api('GET', '/repo')
    def get_repo(req):
        resp = requests.get('https://api.github.com/users/pygics-app/repos')
        if resp.status_code != 200: raise Exception('could not find repository')
        repos = resp.json()
        result = []
        for repo in repos:
            result.append({'name' : repo['name'], 'description' : repo['description']})
        return result
    
    @api('POST', '/repo')
    def load_repo(req, name, branch='master'):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: raise Exception('incorrect uuid')
        return __load_repo_module__(name, branch)
    
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
        
    #===========================================================================
    # Load Modules
    #===========================================================================
    for module in libraries: __load_module__(module, static=True)
    try:
        with open(PYGICS.DIR.SVC + '/modules.prio', 'r') as fd: upload_modules = json.loads(fd.read())
    except Exception as e:
        PYGICS.MNG.MLOG.exception(str(e))
    else:
        for module in upload_modules:
            if os.path.isfile(PYGICS.DIR.MOD + '/' + module + '.py'):
                __load_module__(PYGICS.DIR.MOD + '/' + module + '.py')
            elif os.path.isdir(PYGICS.DIR.MOD + '/' + module):
                __load_module__(PYGICS.DIR.MOD + '/' + module)
    
    #===========================================================================
    # Run Server
    #===========================================================================
    WSGIServer((ip, port),
               application=__pygics_wsgi_application__,
               log=PYGICS.MNG.PLOG,
               error_log=PYGICS.MNG.PLOG).serve_forever()
    