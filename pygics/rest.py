'''
Created on 2017. 2. 28.

@author: Hye-Churn Jang
'''

import requests

import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()

from .task import Lock, Task

class RestAPI:
    
    DEFAULT_CONN_SIZE = requests.adapters.DEFAULT_POOLSIZE
    DEFAULT_CONN_MAX = requests.adapters.DEFAULT_POOLSIZE
    DEFAULT_CONN_RETRY = 3
    PROTO_HTTP = 'http://'
    PROTO_HTTPS = 'https://'
    REFRESH_OFF = 0
        
    # Need Implementation 
    def __login__(self, req):
        # Return Token
        return None
    
    def __refresh__(self, req):
        # Return Token
        return None
    
    def __header__(self):
        # Return Headers
        return None
    
    def __cookie__(self):
        # Return Cookies
        return None
    
    # Exception
    class ExceptSession(Exception):
        
        def __init__(self, api, exp):
            Exception.__init__(self, '[Error]RestAPI:Session:%s:%s' % (api.url, str(exp)))
            if api.debug: print('[Error]RestAPI:Session:%s:%s' % (api.url, str(exp)))
    
    class ExceptMessage(Exception):
        
        def __init__(self, api, method, url, exp=None):
            Exception.__init__(self, '[Error]RestAPI:Message:%s:%s:%s' % (method, url, str(exp)))
            if api.debug: print('[Error]RestAPI:Message:%s:%s:%s' % (method, url, str(exp)))
    
    # Background Worker
    class RefreshWork(Task):
        
        def __init__(self, rest_api, refresh):
            Task.__init__(self, refresh, refresh)
            self.rest_api = rest_api
        
        def run(self):
            try: self.rest_api.refresh()
            except Exception as e:
                if self.rest_api.debug: print('[Error]RestAPI:RefreshWork:%s' % str(e))
    
    # Operation Methods
    def __init__(self, ip,
                 user=None, pwd=None,
                 proto=PROTO_HTTP,
                 conns=DEFAULT_CONN_SIZE,
                 conn_max=DEFAULT_CONN_MAX,
                 retry=DEFAULT_CONN_RETRY,
                 refresh=REFRESH_OFF,
                 debug=False):
        
        self.ip = ip
        self.user = user
        self.pwd = pwd
        self.proto = proto
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.refresh = refresh
        self.debug = debug
        
        self.url = proto + ip
        
        self.session = None
        
        self._restapi_refresh_work = None
        self._restapi_lock_refresh = Lock()
        self._restapi_lock_message = Lock()
        
        if proto == RestAPI.PROTO_HTTPS:
            try:
                import requests.packages
                requests.packages.urllib3.disable_warnings()
            except: pass
        
        self.__init_session__()
        
        try: self.token = self.__login__(self.session)
        except Exception as e: raise RestAPI.ExceptSession(self, e)
        
        if refresh != RestAPI.REFRESH_OFF:
            self._restapi_refresh_work = RestAPI.RefreshWork(self, refresh)
            self._restapi_refresh_work.start()
    
    def __init_session__(self):
        if self.session != None: self.session.close()
        self.session = requests.Session()
        self.session.mount(self.proto,
                           requests.adapters.HTTPAdapter(pool_connections=self.conns,
                                                         pool_maxsize=self.conn_max,
                                                         max_retries=self.retry))
    
    def __send_rest__(self, mtype, url, data=None):
        headers = self.__header__()
        cookies = self.__cookie__()
        
        context = {'verify' : False}
        if headers != None: context['headers'] = headers
        if cookies != None: context['cookies'] = cookies
        
        req_url = self.url + url

        while True:
            self._restapi_lock_message.acquire()
            self._restapi_lock_message.release()
            try:
                if mtype == 'GET': resp = self.session.get(req_url, **context); break
                elif mtype == 'POST': resp = self.session.post(req_url, data=data, **context); break
                elif mtype == 'PUT': resp = self.session.put(req_url, data=data, **context); break
                elif mtype == 'DELETE': resp = self.session.delete(req_url, **context); break
                raise RestAPI.ExceptMessage(mtype, req_url, 'Unknown Method')
            except RestAPI.ExceptMessage as e: raise e
            except: self.refresh()
        
        if self.debug: print('%s:%d:%s\n%s' % (mtype, resp.status_code, url, resp.text))
        return resp
    
    # User Interface
    def refresh(self):
        if self._restapi_lock_refresh.acquire(blocking=False):
            self._restapi_lock_message.acquire()
            if self.debug: print('[Info]RestAPI:RefreshRequest:%s' % self.url)
            try: self.token = self.__refresh__(self.session)
            except Exception as e:
                if self.debug: print('[Error]RestAPI:Refresh:__refresh__():%s' % str(e))
                try:
                    self.__init_session__()
                    self.token = self.__login__(self.session)
                except Exception as e:
                    if self.debug: print('[Error]RestAPI:Refresh:__login__():%s' % str(e))
                    self._restapi_lock_message.release()
                    self._restapi_lock_refresh.release()
                    raise RestAPI.ExceptSession(self, e)
            if self.debug: print('[Info]RestAPI:RefreshUpdated:%s' % self.url)
            self._restapi_lock_message.release()
            self._restapi_lock_refresh.release()
        
    def close(self):
        if self.session != None:
            if self._restapi_refresh_work != None: self._restapi_refresh_work.stop()
            self.session.close()
            self.session = None
    
    def get(self, url): return self.__send_rest__('GET', url)
    
    def post(self, url, data): return self.__send_rest__('POST', url, data)
    
    def put(self, url, data): return self.__send_rest__('PUT', url, data)
    
    def delete(self, url): return self.__send_rest__('DELETE', url)
