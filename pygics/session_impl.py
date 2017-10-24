# -*- coding: utf-8 -*-
'''
Created on 2017. 10. 19.
@author: HyechurnJang
'''

import requests

from .task import Lock, Task

class RestImpl:

    #===========================================================================
    # Static Vars    
    #===========================================================================
    DEFAULT_CONN_SIZE = requests.adapters.DEFAULT_POOLSIZE
    DEFAULT_CONN_MAX = requests.adapters.DEFAULT_POOLSIZE
    DEFAULT_CONN_RETRY = 3
    REFRESH_OFF = 0
    
    #===========================================================================
    # Exceptions
    #===========================================================================
    class ExceptSession(Exception):
        def __init__(self, rest, exp): Exception.__init__(self, '[Error]Rest:Session:%s>>%s' % (rest.url, str(exp)))
    
    class ExceptMessage(Exception):
        def __init__(self, rest, method, url, exp=None): Exception.__init__(self, '[Error]Rest:Message:%s:%s>>%s' % (method, rest.url + url, str(exp)))
    
    #===========================================================================
    # Session Refresh Worker
    #===========================================================================
    class __Refresher__(Task):
        
        def __init__(self, rest):
            Task.__init__(self, rest.refresh_sec, rest.refresh_sec)
            self.rest = rest
            self.start()
        
        def __run__(self):
            try: self.rest.refresh()
            except Exception as e:
                if self.rest.debug: print('[Error]Rest:Refresher>>%s' % str(e))
    
    #===========================================================================
    # Methods
    #===========================================================================
    def __init__(self, url, usr, pwd, conns, max_conns, retry, refresh_sec, debug):
        self.url = url
        self.usr = usr
        self.pwd = pwd
        self.session = None
        if 'https://' in url.lower():
            self._pygics_rest_secure = True
            self.proto = 'https://'
        else:
            self._pygics_rest_secure = False
            self.proto = 'http://'
        self.conns = conns
        self.max_conns = max_conns
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
        self._pygics_rest_refresh_work = None
        self._pygics_rest_lock_refresh = Lock()
        self._pygics_rest_lock_message = Lock()
        
        if self._pygics_rest_secure:
            try:
                import requests.packages
                requests.packages.urllib3.disable_warnings()
            except: pass
        
        self.__init_session__()
        self.token = self.__login__(self.session)
        if refresh_sec != RestImpl.REFRESH_OFF:
            self._pygics_rest_refresh_work = RestImpl.__Refresher__(self)
    
    def __init_session__(self):
        if self.session: self.session.close()
        self.session = requests.Session()
        self.session.mount(self.proto,
                           requests.adapters.HTTPAdapter(pool_connections=self.conns,
                                                         pool_maxsize=self.max_conns,
                                                         max_retries=self.retry))
    
    def __send_rest__(self, method, url, data=None):
        headers = self.__header__()
        cookies = self.__cookie__()
        
        context = {'verify' : False}
        if headers: context['headers'] = headers
        if cookies: context['cookies'] = cookies
        
        url = self.url + url

        while True:
            self._pygics_rest_lock_message.on()
            self._pygics_rest_lock_message.off()
            try:
                if method == 'GET': resp = self.session.get(url, **context); break
                elif method == 'POST': resp = self.session.post(url, data=data, **context); break
                elif method == 'PUT': resp = self.session.put(url, data=data, **context); break
                elif method == 'DELETE': resp = self.session.delete(url, **context); break
                else: raise RestImpl.ExceptMessage(method, url, 'Unknown Method')
            except RestImpl.ExceptMessage as e: raise e
            except: self.refresh()
        
        if self.debug:
            if data != None: print('%s:%s>>%d\n%s\n%s\n%s' % (method, url, resp.status_code, context, data, resp.text))
            else: print('%s:%s>>%d\n%s\n%s' % (method, url, resp.status_code, context, resp.text))
        return resp
    
    def refresh(self):
        if self._pygics_rest_lock_refresh.on(block=False):
            self._pygics_rest_lock_message.on()
            if self.debug: print('[Info]Rest:Refresh:%s' % self.url)
            try: self.token = self.__refresh__(self.session)
            except Exception as e:
                if self.debug: print('[Error]Rest:Refresh:%s>>%s' % (self.url, str(e)))
                try:
                    self.__init_session__()
                    self.token = self.__login__(self.session)
                except Exception as e:
                    if self.debug: print('[Error]Rest:Refresh:%s>>' % (self.url, str(e)))
                    self._pygics_rest_lock_message.off()
                    self._pygics_rest_lock_refresh.off()
                    raise RestImpl.ExceptSession(self, e)
            if self.debug: print('[Info]RestAPI:RefreshUpdated:%s' % self.url)
            self._pygics_rest_lock_message.off()
            self._pygics_rest_lock_refresh.off()
        
    def close(self):
        if self.session:
            if self._pygics_rest_refresh_work: self._pygics_rest_refresh_work.stop()
            self.session.close()
            self.session = None
    
    def get(self, url): return self.__send_rest__('GET', url)
    
    def post(self, url, data): return self.__send_rest__('POST', url, data)
    
    def put(self, url, data): return self.__send_rest__('PUT', url, data)
    
    def delete(self, url): return self.__send_rest__('DELETE', url)
