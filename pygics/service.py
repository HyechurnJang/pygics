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
import logging
import logging.handlers
from gevent.pywsgi import WSGIServer
from .task import Task

class __PygicsServiceEnvironment__:
    
    class __PygicsServiceDirectory__:
        ROOT = os.path.expanduser('~') + '/.pygics'
        SVC = None
        MOD = None
    
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
            kv = re.match('(?P<key>\w+)=("|%22|%27)?(?P<val>[\w]+)("|%22|%27)?', q)
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

def api(method, url):
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
            res('200 OK', [('Content-Type', 'application/json')])
            return json.dumps({'result' : ret})
        
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

def model(database):
    def model_wrapper(model):
        def decofunc(req, res):
            print req
            print database
            print model
            res('200 OK', [('Content-Type', 'application/json')])
            return json.dumps({'result' : True})
        
        __PygicsServiceEnvironment__.__environment_init__()
        
        #=======================================================================
        # get names
        #=======================================================================
        module_name = model.__module__
        model_name = model.__name__
        
        #=======================================================================
        # get dn
        #=======================================================================
        if module_name == '__main__': dn = '/' + model_name
        elif module_name == 'pygics.service': dn = '/pygics/%s' % model_name
        else: dn = '/%s/%s' % (module_name, model_name)
        
        #=======================================================================
        # get rns
        #=======================================================================
        rns = filter(None, dn.split('/'))
        
        #=======================================================================
        # register
        #=======================================================================
        for method in PYGICS.REST:
            ref = PYGICS.REST[method.upper()]
            for rn in rns:
                if rn not in ref: ref[rn] = {}
                ref = ref[rn]
            ref['__api_url__'] = dn
            ref['__api_ref__'] = decofunc
            print('register api <%s:%s> link to <%s.%s>' % (method, dn, module_name, model_name))
            
        return decofunc
    return model_wrapper

def server(ip, port, static_modules=[], clean_init=False):
    
    #===========================================================================
    # Initial Setup
    #===========================================================================
    __PygicsServiceEnvironment__.__environment_init__()
    PYGICS.__service_init__(ip, port, clean_init)
    
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
        try: return req.api(req, res)
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
    
    def __load_module__(file_path, static=False):
        if os.path.isfile(file_path):
            directory, file_name = os.path.split(file_path)
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
        raise Exception('non-exist module')
    
    @api('GET', '/module')
    def get_module(req):
        return {'static' : PYGICS.MOD.STATIC, 'upload' : PYGICS.MOD.UPLOAD}
    
    @api('POST', '/module')
    def load_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: return {'error' : 'incorrect uuid'}
        file_path = PYGICS.DIR.MOD + '/' + name + '.py'
        with open(file_path, 'wb') as fd: fd.write(req.data)
        return __load_module__(file_path)
    
    @api('DELETE', '/module')
    def del_module(req, name):
        if 'PYGICS_UUID' not in req.header or req.header['PYGICS_UUID'] != PYGICS.MNG.UUID: return {'error' : 'incorrect uuid'}
        file_path_py = PYGICS.DIR.MOD + '/' + name + '.py'
        file_path_pyc = file_path_py + 'c'
        if os.path.exists(file_path_py):
            ret = __delete_module__(name)
            os.remove(file_path_py)
            if os.path.exists(file_path_pyc): os.remove(file_path_pyc)
            return ret
        raise Exception('non-exist module')
    
    #===========================================================================
    # Load Modules
    #===========================================================================
    for module in static_modules: __load_module__(module, static=True)
    try:
        with open(PYGICS.DIR.SVC + '/modules.prio', 'r') as fd: upload_modules = json.loads(fd.read())
    except Exception as e:
        PYGICS.MNG.MLOG.exception(str(e))
    else:
        for module in upload_modules: __load_module__(PYGICS.DIR.MOD + '/' + module + '.py')
    
    #===========================================================================
    # Run Server
    #===========================================================================
    WSGIServer((ip, port),
               application=__pygics_wsgi_application__,
               log=PYGICS.MNG.PLOG,
               error_log=PYGICS.MNG.PLOG).serve_forever()
    