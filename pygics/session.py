# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 20.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

from jzlib import Inventory, Mortal
from .session_impl import RestImpl

class Rest(Mortal, Inventory, RestImpl):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self,
                 url, usr=None, pwd=None,
                 conns=RestImpl.DEFAULT_CONN_SIZE,
                 max_conns=RestImpl.DEFAULT_CONN_MAX,
                 retry=RestImpl.DEFAULT_CONN_RETRY,
                 refresh_sec=RestImpl.REFRESH_OFF,
                 debug=False):
        RestImpl.__init__(self, url, usr, pwd, conns, max_conns, retry, refresh_sec, debug)
        Inventory.__init__(self)
    
    def __dead__(self): RestImpl.close(self)
    
    #===========================================================================
    # Implementations 
    #===========================================================================
    def __login__(self, session): return None # Return Token
    
    def __refresh__(self, session): return None # Return Token
    
    def __header__(self): return None # Return Headers
    
    def __cookie__(self): return None # Return Cookies
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def get(self, url): return RestImpl.get(self, url)
    
    def post(self, url, data): return RestImpl.post(self, url, data)
    
    def put(self, url, data): return RestImpl.put(self, url, data)
    
    def delete(self, url): return RestImpl.delete(self, url)
    
    def close(self): RestImpl.close(self)
