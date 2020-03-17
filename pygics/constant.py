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

from mimetypes import MimeTypes
import sqlalchemy
from .common import dumpJson


class HttpMethodType:
    
    #===========================================================================
    # Constant Values
    #===========================================================================
    Get = 'GET'
    Post = 'POST'
    Put = 'PUT'
    Patch = 'PATCH'
    Delete = 'DELETE'
    
    SupportList = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']


class HttpContentType:
    
    #===========================================================================
    # Constant Values
    #===========================================================================
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
    
    #===========================================================================
    # Class Methods
    #===========================================================================
    __MTOBJ__ = MimeTypes()

    @classmethod
    def getType(cls, path):
        mimetype, _ = cls.__MTOBJ__.guess_type(path)
        if not mimetype: return HttpContentType.AppStream
        return mimetype


class HttpResponseType:
    
    #===========================================================================
    # Abstract
    #===========================================================================
    class __HTTP__(Exception):

        def __init__(self, status, headers, data):
            self.status = status
            self.headers = headers
            self.data = data
    
    class __ERROR__(__HTTP__, Exception):
         
        def __init__(self, status, headers, data):
            headers.append(('Content-Type', HttpContentType.AppJson))
            HttpResponseType.__HTTP__.__init__(self, status, headers, dumpJson({'error' : data}))
            Exception.__init__(self, data)
    
    #===========================================================================
    # Class Object & Methods
    #===========================================================================
    class OK(__HTTP__):  # 200

        def __init__(self, data='', headers=[]):
            HttpResponseType.__HTTP__.__init__(self, '200 OK', headers, data)
             
    class Redirect(__HTTP__):  # 302

        def __init__(self, url, headers=[]):
            headers.append(('Location', url))
            HttpResponseType.__HTTP__.__init__(self, '302 Found', headers, '')
     
    @classmethod
    def BadRequest(cls, data='bad request', headers=[], exception=True):  # 400
        
        class __BadRequest__(HttpResponseType.__ERROR__):

            def __init__(self, headers, data):
                HttpResponseType.__ERROR__.__init__(self, '400 Bad Request', headers, data)
        
        obj = __BadRequest__(headers, data)
        if exception: raise obj
        else: return obj 
    
    @classmethod
    def Unauthorized(cls, data='bad request', headers=[], exception=True):  # 401
        
        class __Unauthorized__(HttpResponseType.__ERROR__):

            def __init__(self, headers, data):
                headers.append(('WWW-Authenticate', 'Basic realm="pygics"'))
                HttpResponseType.__ERROR__.__init__(self, '401 Unauthorized', headers, data)
        
        obj = __Unauthorized__(headers, data)
        if exception: raise obj
        else: return obj 
    
    @classmethod
    def Forbidden(cls, data='forbidden', headers=[], exception=True):  # 403

        class __Forbidden__(HttpResponseType.__ERROR__):  # 403
    
            def __init__(self, headers, data):
                HttpResponseType.__ERROR__.__init__(self, '403 Forbidden', headers, data)
        
        obj = __Forbidden__(headers, data)
        if exception: raise obj
        else: return obj 
    
    @classmethod
    def NotFound(cls, data='not found', headers=[], exception=True):  # 404

        class __NotFound__(HttpResponseType.__ERROR__):  # 404
    
            def __init__(self, headers, data):
                HttpResponseType.__ERROR__.__init__(self, '404 Not Found', headers, data)
        
        obj = __NotFound__(headers, data)
        if exception: raise obj
        else: return obj 
    
    @classmethod
    def ServerError(cls, data='internal server error', headers=[], exception=True):  # 500

        class __ServerError__(HttpResponseType.__ERROR__):
    
            def __init__(self, headers=[], data='internal server error'):
                HttpResponseType.__ERROR__.__init__(self, '500 Internal Server Error', headers, data)
        
        obj = __ServerError__(headers, data)
        if exception: raise obj
        else: return obj 
    
    @classmethod
    def NotImplemented(cls, data='not implemented', headers=[], exception=True):  # 501

        class __NotImplemented__(HttpResponseType.__ERROR__):
    
            def __init__(self, headers=[], data='not implemented'):
                HttpResponseType.__ERROR__.__init__(self, '501 Not Implemented', headers, data)
        
        obj = __NotImplemented__(headers, data)
        if exception: raise obj
        else: return obj 

class Schema:
    
    Column = sqlalchemy.Column
    String = sqlalchemy.String
    Integer = sqlalchemy.Integer
    Float = sqlalchemy.Float
    DateTime = sqlalchemy.DateTime
    Boolean = sqlalchemy.Boolean
    
    