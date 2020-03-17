# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 2. 15.
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

from .common import logDebug, dumpJson

def debug(func):
    
    def wrapper(req, *args, **kargs):
        logDebug('[Before Action]\nURL : %s %s\nHeaders : %s\nCookies : %s\nReceived Data is %s' % (
            req.method,
            req.url,
            dumpJson(req.headers, indent=2),
            dumpJson(req.cookies, indent=2),
            'exists' if req.data else 'empty'))
        
        ret = func(req, *args, **kargs)
        
        logDebug('[After Action]\nURL : %s %s\nAdd Headers : %s\nAdd Cookies : %s\nSending Data is %s' % (
            req.method,
            req.url,
            dumpJson(req.headers_add, indent=2),
            dumpJson(req.cookies_add, indent=2),
            'exists' if ret else 'empty'))
        
        return ret
    
    return wrapper