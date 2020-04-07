# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 3. 9..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import urllib3
urllib3.disable_warnings()
from builtins import staticmethod
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import mapper
from sqlalchemy.orm import Session
from sqlalchemy import Table as saTable, MetaData
from inspect import isclass
from .common import dumpJson, logDebug
from .struct import PygObj, singleton
from .task import Lock, sleep


class Driver(PygObj):
    
    #===========================================================================
    # End User Interface
    #===========================================================================
    def system(self, *args, **kwargs): pass


def sdk(client):
    return singleton(client, st_namespace='SDK', st_name=client.__name__)

#===============================================================================
# Pygics Component Client SDK
#===============================================================================


class ClientPath(PygObj):
    
    def __init__(self, session, method, init_path):
        self.__session__ = session
        self.__method__ = method
        self.__path__ = init_path
    
    def __getattr__(self, path):
        self.__path__ = '%s/%s' % (self.__path__, path)
        return self
    
    def __call__(self, *args, **kwargs):
        if args:
            for arg in args:
                self.__path__ = '%s/%s' % (self.__path__, str(arg))
        if self.__method__ == 'GET':
            resp = self.__session__.get(self.__path__)
        elif self.__method__ == 'POST':
            resp = self.__session__.post(self.__path__, json=kwargs)
        elif self.__method__ == 'PUT':
            resp = self.__session__.put(self.__path__, json=kwargs)
        elif self.__method__ == 'DELETE':
            resp = self.__session__.delete(self.__path__)
        else:
            raise Exception('can not execute unsupported method %s' % self.__method__)
        resp.raise_for_status()
        return resp.json()
            

class Client(Driver):
    
    def __init__(self, host, port, base_url):
        self.init_path = 'http://%s:%d%s' % (host, port, base_url)
        self.session = requests.Session()
    
    @property
    def GET(self):
        return ClientPath(self.session, 'GET', self.init_path)
    
    @property
    def POST(self):
        return ClientPath(self.session, 'POST', self.init_path)
    
    @property
    def PUT(self):
        return ClientPath(self.session, 'PUT', self.init_path)
    
    @property
    def DELETE(self):
        return ClientPath(self.session, 'DELETE', self.init_path)


#===============================================================================
# Rest API SDK
#===============================================================================
class ModelList(list):
            
    def __init__(self, model, api=None, parent=None):
        list.__init__(self)
        self.model = model
        self.api = api
        self.parent = parent
        self.list_layer = model.__meta__.list_layer
        self.layer = model.__meta__.layer
    
    def __call__(self, **kwargs):
        data = self.model.__new__(self.model)
        data.__data__(**kwargs)
        if self.parent:
            data.__parent__ = self.parent
        self.append(data)
        
        
class Model(dict):

    #===========================================================================
    # Custom Filter Interface    
    #===========================================================================
    @staticmethod
    def __create_filter__(model, intent): pass
    
    @staticmethod
    def __list_filter__(model, clause): pass
    
    @staticmethod
    def __get_filter__(model, args, keys): pass
    
    @staticmethod
    def __update_filter__(model): pass
    
    @staticmethod
    def __delete_filter__(model): pass
    
    #===========================================================================
    # Class Wrapper for Class Status
    #===========================================================================
    @classmethod
    def __class_create_wrapper__(cls, **intent):
        cls.__create_filter__(cls, intent)
        return Rest.__create_wrapper__(cls, **intent)
    
    @classmethod
    def __class_list_wrapper__(cls, **clause):
        cls.__list_filter__(cls, clause)
        return Rest.__list_wrapper__(ModelList(cls, cls.__meta__.api), **clause)
    
    @classmethod
    def __class_get_wrapper__(cls, *args, **keys):
        args = list(args)
        cls.__get_filter__(cls, args, keys)
        return Rest.__get_wrapper__(cls, *args, **keys)
    
    #===========================================================================
    # Init Wrapper for Class Status
    #===========================================================================
    def __init_create_wrapper__(self, **intent):
        self.__create_filter__(self, intent)
        Rest.__create_wrapper__(self, **intent)
    
    def __init_get_wrapper__(self, *args, **keys):
        self.__get_filter__(self, args, keys)
        Rest.__get_wrapper__(self, *args, **keys)
    
    def __init_wrapper__(self, *args, **kwargs):
        self.__data__(**kwargs)
    
    #===========================================================================
    # Inst Wrapper for Instance Status
    #===========================================================================
    def __inst_create_wrapper__(self, **intent):
        self.__create_filter__(self, intent)
        data = self.__class__.__new__(self.__class__)
        data.__parent__ = self.__parent__
        return Rest.__create_wrapper__(data, **intent)
    
    def __inst_list_wrapper__(self, **clause):
        self.__list_filter__(self, clause)
        data = ModelList(self.__class__, self.__api__(), self.__parent__)
        return Rest.__list_wrapper__(data, **clause)
    
    def __inst_get_wrapper__(self, *args, **keys):
        args = list(args)
        self.__get_filter__(self, args, keys)
        data = self.__class__.__new__(self.__class__)
        data.__parent__ = self.__parent__
        return Rest.__get_wrapper__(data, *args, **keys)
    
    def __inst_update_wrapper__(self):
        self.__update_filter__(self)
        return Rest.__update_wrapper__(self)
    
    def __inst_delete_wrapper__(self):
        self.__delete_filter__(self)
        return Rest.__delete_wrapper__(self)
    
    #===========================================================================
    # Call Wrapper for Instance Status
    #===========================================================================
    def __call_create_wrapper__(self, **intent):
        return self.create(**intent)
    
    def __call_get_wrapper__(self, *args, **keys):
        return self.get(*args, **keys)
    
    def __call_wrapper__(self, *args, **kwargs):
        return self.__data__(**kwargs)
    
    #===========================================================================
    # Internal Data Actions
    #===========================================================================
    @classmethod
    def __model__(cls, **kwargs):
        model = cls.__new__(cls)
        return model.__data__(**kwargs)
    
    @classmethod
    def __help__(cls):
        call = None
        life = []
        prop = []
        subm = []
        func = []
        
        for name, attr in cls.__dict__.items():
            attr_type = str(type(attr))
            attr_addr = str(attr)
            if 'property' in attr_type:
                prop.append(name)
            elif 'function' in attr_type:
                if '__inst_' in attr_addr:
                    if '__inst_' not in name:
                        life.append(name + '()')
                elif '__' not in name:
                    func.append(name + '()')
                elif '__init_wrapper__' == name:
                    if '__init_get_wrapper__' in attr_addr:
                        call = 'get()'
                    elif '__init_create_wrapper__' in attr_addr:
                        call = 'create()'
            elif 'type' in attr_type and issubclass(attr, Model):
                if hasattr(attr.__meta__, 'property'):
                    prop.append(name)
                else:
                    subm.append(name)
            elif 'method' in attr_type:
                if '__class_' in attr_addr:
                    if '__class_' not in name:
                        life.append(name + '()')
        
        return '''{name}
  CRUD Actions (self calling action is "{call}"){life}
  Properties:{prop}
  Sub-Models:{subm}
  Defined Actions:{func}{intent}'''.format(
            name=cls.__name__,
            call=call,
            life='\n    - ' + '\n    - '.join(life) if life else '\n      N/A',
            prop='\n    - ' + '\n    - '.join(prop) if prop else '\n      N/A',
            subm='\n    - ' + '\n    - '.join(subm) if subm else '\n      N/A',
            func='\n    - ' + '\n    - '.join(func) if func else '\n      N/A',
            intent='\n  Model Intent\n  {}'.format(cls.__doc__) if cls.__doc__ else '')
    
    def __init__(self, *args, **kwargs):
        self.__init_wrapper__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.__call_wrapper__(*args, **kwargs)
    
    def __data__(self, **kwargs):
        dict.__init__(self, **kwargs)
        return self
    
    def __keys__(self, keys=None):
        if keys == None: keys = {}
        if hasattr(self, '__parent__'):
            keys = self.__parent__.__keys__(keys)
        for k, v in self.__meta__.keys.items():
            if k not in keys and v in self:
                keys[k] = self[v]
        return keys
    
    def __api__(self, sub_url=None, keys=None):
        api = self.__meta__.api
        if sub_url:
            api = api + sub_url
        return api.format(**(self.__keys__(keys)))
    
    def __url__(self, sub_url=None, keys=None):
        url = self.__meta__.url
        if sub_url:
            url = url + sub_url
        return url.format(**(self.__keys__(keys)))
    
    def __repr__(self):
        return '<%s>%s' % (self.__class__.__name__, dumpJson(dict(**self), indent=2))
    
    def __neg__(self):
        if hasattr(self, '__parent__'):
            return self.__parent__
        else: self
    
    def __getattribute__(self, name):
        if name in self: return self[name]
        else:
            attr = dict.__getattribute__(self, name)
            if isclass(attr) and issubclass(attr, Model) and attr != dict.__getattribute__(self, '__class__'):
                model = attr.__new__(attr)
                model.__parent__ = self
                if hasattr(attr, 'create'):
                    model.create = model.__inst_create_wrapper__
                    if model.__meta__.def_func == 'create':
                        model.__call_wrapper__ = model.__call_create_wrapper__
                if hasattr(attr, 'list'):
                    model.list = model.__inst_list_wrapper__
                if hasattr(attr, 'get'):
                    model.get = model.__inst_get_wrapper__
                    if model.__meta__.def_func == 'get':
                        model.__call_wrapper__ = model.__call_get_wrapper__
                if hasattr(model.__meta__, 'property'):
                    model.__meta__.driver.__get__(model.__url__(), model)
                dict.__setattr__(self, name, model)
                return model
            return attr


class RestUser:
            
    def __init__(self, sdk, url, username, password, retry=3):
        self.sdk = sdk
        self.url = url
        self.username = username
        self.password = password
        self.retry = retry
        self.sdk.lock.on()
        self.sdk.account = self
        self.__session__()
        self.__headers__()
        self.__cookies__()
        self.sdk.account = self.sdk.default
        self.sdk.lock.off()
        
    def __session__(self):
        self.session = requests.Session()
        self.session.verify = False
    
    def __headers__(self, **kwargs):
        for k, v in kwargs.items():
            self.session.headers[k] = v
    
    def __cookies__(self, **kwargs):
        for k, v in kwargs.items():
            self.session.cookies[k] = v
    
    def __refresh__(self):
        self.__headers__()
        self.__cookies__()
    
    def __enter__(self):
        self.sdk.lock.on()
        self.sdk.account = self
        return self
        
    def __exit__(self, type, value, traceback):
        self.sdk.account = self.sdk.default
        self.sdk.lock.off()

    
class Rest(Driver):
    
    def __init__(self, user_model=RestUser, list_layer=[], layer=[]):
        self.user_model = user_model
        self.list_layer = list_layer
        self.layer = layer
        self.account = None
        self.default = None
        self.lock = Lock()
    
    def system(self, url, username, password):
        self.default = self.user_model(self, url, username, password)
        self.account = self.default
        return self.default
    
    def login(self, username, password, url=None):
        if not url and not self.default:
            raise Exception('could not find rest api host')
        elif not url: url = self.default.url
        return self.user_model(self, url, username, password)
    
    #===========================================================================
    # Interface for Rest Data Handling
    #===========================================================================
    def __create__(self, api, data, intent):
        resp = self.doPostMethod(api, intent)
        if resp.text:
            json_data = resp.json()
            for layer in data.__meta__.layer:
                json_data = json_data[layer]
        else:
            json_data = {}
        data.__data__(**json_data)
    
    def __list__(self, api, list_of_data, clause):
        if clause:
            query = '&'.join(['%s=%s' % (k, str(v)) for k, v in clause.items()])
            api = '%s?%s' % (api, query)
        resp = self.doGetMethod(api)
        if resp.text:
            json_list_data = resp.json()
            for list_layer in list_of_data.list_layer:
                json_list_data = json_list_data[list_layer]
        else:
            json_list_data = []
        for json_data in json_list_data:
            for layer in list_of_data.layer:
                json_data = json_data[layer]
            list_of_data(**json_data)
    
    def __get__(self, url, data):
        resp = self.doGetMethod(url)
        if resp.text:
            json_data = resp.json()
            for layer in data.__meta__.layer:
                json_data = json_data[layer]
        else:
            json_data = {}
        data.__data__(**json_data)
        
    def __update_using_put__(self, url, data):
        resp = self.doPutMethod(url, data)
        if resp.text:
            json_data = resp.json()
            for layer in data.__meta__.layer:
                json_data = json_data[layer]
        else:
            json_data = {}
        data.__data__(**json_data)
    
    def __update_using_patch__(self, url, data):
        resp = self.doPatchMethod(url, data)
        if resp.text:
            json_data = resp.json()
            for layer in data.__meta__.layer:
                json_data = json_data[layer]
        else:
            json_data = {}
        data.__data__(**json_data)
    
    def __update_using_post__(self, url, data):
        resp = self.doPostMethod(url, data)
        if resp.text:
            json_data = resp.json()
            for layer in data.__meta__.layer:
                json_data = json_data[layer]
        else:
            json_data = {}
        data.__data__(**json_data)
    
    def __delete__(self, url, data):
        self.doDeleteMethod(url)
        data.__deleted__ = True
    
    #===========================================================================
    # Rest CRUD Wrapper
    #===========================================================================
    @staticmethod
    def __create_wrapper__(model, **intent):
        if isinstance(model, Model):
            api = model.__api__()
            data = model
        else:
            api = model.__meta__.api
            data = model.__new__(model)
        model.__meta__.driver.__create__(api, data, intent)
        return data
    
    @staticmethod
    def __list_wrapper__(list_of_data, **clause):
        list_of_data.model.__meta__.driver.__list__(list_of_data.api, list_of_data, clause)
        return list_of_data
    
    @staticmethod
    def __get_wrapper__(model, *args, **keys):
        if len(args) == 1:
            keys[model.__meta__.keys_path[0]] = args[0]
        if isinstance(model, Model):
            url = model.__url__(keys=keys)
            data = model
        else:
            url = model.__meta__.url.format(**keys)
            data = model.__new__(model)
        model.__meta__.driver.__get__(url, data)
        return data
    
    @staticmethod
    def __update_wrapper__(model):
        url = model.__url__()
        if model.__meta__.def_update == 'put':
            model.__meta__.driver.__update_using_put__(url, model)
        elif model.__meta__.def_update == 'patch':
            model.__meta__.driver.__update_using_patch__(url, model)
        elif model.__meta__.def_update == 'post':
            model.__meta__.driver.__update_using_post__(url, model)
        else:
            raise Exception('undefined default update driver')
        return model
    
    @staticmethod
    def __delete_wrapper__(model):
        url = model.__url__()
        model.__meta__.driver.__delete__(url, model)
        return model
    
    #===========================================================================
    # HTTP Methods
    #===========================================================================
    def doGetMethod(self, url):
        logDebug('[%s SDK] GET > %s' % (self.__class__.__name__, url))
        for delay in range(0, self.account.retry):
            resp = self.account.session.get(self.account.url + url)
            if resp.status_code == 401:
                logDebug('[%s SDK] Refresh Session')
                sleep(delay)
                self.account.__refresh__()
                continue
            resp.raise_for_status()
            break
        return resp
    
    def doPostMethod(self, url, data=None):
        if data == None: data = {}
        logDebug('[%s SDK] POST > %s < %s' % (self.__class__.__name__, url, dumpJson(data)))
        for delay in range(0, self.account.retry):
            resp = self.account.session.post(self.account.url + url, json=data)
            if resp.status_code == 401:
                logDebug('[%s SDK] Refresh Session')
                sleep(delay)
                self.account.__refresh__()
                continue
            resp.raise_for_status()
            break
        return resp
    
    def doPutMethod(self, url, data=None):
        if data == None: data = {}
        logDebug('[%s SDK] PUT > %s < %s' % (self.__class__.__name__, url, dumpJson(data)))
        for delay in range(0, self.account.retry):
            resp = self.account.session.put(self.account.url + url, json=data)
            if resp.status_code == 401:
                logDebug('[%s SDK] Refresh Session')
                sleep(delay)
                self.account.__refresh__()
                continue
            resp.raise_for_status()
            break
        return resp
    
    def doPatchMethod(self, url, data=None):
        if data == None: data = {}
        logDebug('[%s SDK] PATCH > %s < %s' % (self.__class__.__name__, url, dumpJson(data)))
        for delay in range(0, self.account.retry):
            resp = self.account.session.patch(self.account.url + url, json=data)
            if resp.status_code == 401:
                logDebug('[%s SDK] Refresh Session')
                sleep(delay)
                self.account.__refresh__()
                continue
            resp.raise_for_status()
            break
        return resp
    
    def doDeleteMethod(self, url):
        logDebug('[%s SDK] DELETE > %s' % (self.__class__.__name__, url))
        for delay in range(0, self.account.retry):
            resp = self.account.session.delete(self.account.url + url)
            if resp.status_code == 401:
                logDebug('[%s SDK] Refresh Session')
                sleep(delay)
                self.account.__refresh__()
                continue
            resp.raise_for_status()
            break
        return resp
    
    #===========================================================================
    # Schema Decorators
    #===========================================================================
    def __call__(self, api=None, url=None, list_layer=None, layer=None, **keys):

        def wrapper(model):
            
            class Meta(object):
                
                def __repr__(self):
                    ret = ['KEY : %s' % self.keys, ]
                    if hasattr(self, 'api'):
                        ret.append('API : %s' % self.api)
                    if hasattr(self, 'url'):
                        ret.append('URL : %s' % self.url)
                    return '\n'.join(ret)
            
            # create metadata
            model.__meta__ = Meta()
            model.__meta__.driver = self
            model.__meta__.def_func = None
            model.__meta__.keys = keys
            model.__meta__.keys_count = len(keys)
            model.__meta__.keys_path = list(keys.keys())
            model.__meta__.keys_data = list(keys.values())
            model.__meta__.list_layer = list_layer if list_layer != None else self.list_layer
            model.__meta__.layer = layer if layer != None else self.layer
            if api != None: model.__meta__.api = api
            if url != None: model.__meta__.url = url
            
            logDebug('[SDK.%s] Register > %s' % (self.__class__.__name__, str(model).split("'")[1]))
            return model

        return wrapper
    
    def entry(self, model):
        model.__meta__.entry = True
        self.__setattr__(model.__name__, model)
        logDebug('[SDK.%s] Register Entry > SDK.%s.%s' % (self.__class__.__name__, self.__class__.__name__, model.__name__))
        return model
    
    def create(self, def_model=None):
        
        def register(model):
            if not def_model:
                model.__meta__.def_func = 'create'
                model.__init_wrapper__ = model.__init_create_wrapper__
            model.create = model.__class_create_wrapper__
            return model
        
        if def_model:
            return register(def_model)
        else:
            return register
        
    def list(self, model):
        model.list = model.__class_list_wrapper__
        return model
        
    def get(self, def_model=None):

        def register(model):
            if not def_model:
                model.__meta__.def_func = 'get'
                model.__init_wrapper__ = model.__init_get_wrapper__
            model.get = model.__class_get_wrapper__
            return model

        if def_model:
            return register(def_model)
        else:
            return register
    
    def update(self, def_method='put'):

        def register(model):
            def_update = def_method.lower()
            if def_update not in ['post', 'put', 'patch']:
                raise Exception('unsupport http method for update')
            model.__meta__.def_update = def_update.lower()
            model.update = model.__inst_update_wrapper__
            return model

        return register
        
    def delete(self, model):
        model.delete = model.__inst_delete_wrapper__
        return model
    
    def property(self, model):
        model.__meta__.property = True
        return model


#===============================================================================
# Database SDK
#===============================================================================
class Table(object):
    
    __schema__ = []
    
    @classmethod
    def list(cls, *clause, **kwargs):
        return cls.query(*clause, **kwargs).all()
    
    @classmethod
    def query(cls, *clause, **kwargs):
        order = kwargs['order'] if 'order' in kwargs else []
        if not isinstance(order, list):
            order = [order]
        query = cls.__driver__.__query__(cls)
        for c in clause:
            query = query.filter(c)
        for o in order:
            query = query.order_by(o)
        return query
    
    def __init__(self, **kargs):
        for k, v in kargs.items():
            self.__setattr__(k, v)
        self.__driver__.__create__(self)
    
    def update(self):
        self.__driver__.__update__()
    
    def delete(self):
        self.__driver__.__delete__(self)


class Database(Driver):
        
    def __init__(self, proto):
        self.proto = proto
        self.metadata = MetaData()
    
    def system(self, host, username=None, password=None):
        self.host = host
        if username and password: self.account = '%s:%s' % (username, password)
        elif username: self.account = username
        else: self.account = ''
        self.url = '%s://%s@%s/%s' % (self.proto, self.account, self.host, self.__class__.__name__.lower())
        self.engine = create_engine(self.url)
        self.session = Session(self.engine)
        self.metadata.create_all(self.engine)
        self.autocommit = True
        self.lock = Lock()
    
    def __call__(self, model):
        name = model.__name__
        args = [name, self.metadata] + model.__schema__
        table = saTable(*args)
        mapper(model, table)
        model.__driver__ = self
        self.__setattr__(name, model)
        return model
    
    def __enter__(self):
        self.autocommit = False
        self.lock.on()
        return self
        
    def __exit__(self, type, value, traceback):
        self.session.commit()
        self.lock.off()
        self.autocommit = True
    
    def __create__(self, data):
        self.session.add(data)
        if self.autocommit:
            self.session.commit()
    
    def __query__(self, cls):
        return self.session.query(cls)
    
    def __update__(self):
        if self.autocommit:
            self.session.commit()
    
    def __delete__(self, data):
        self.session.delete(data)
        if self.autocommit:
            self.session.commit()
