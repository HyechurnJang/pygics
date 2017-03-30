# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 28.
@author: HyechurnJang
'''
import pygics

@pygics.service('GET', '/')
def all(req, *args, **kargs):
    print('all')
    print(req)
    return {'test' : 'ok'}

@pygics.service('GET', '/get')
def get1(req):
    print('get1')
    print(req)
    return {'test' : 'ok'}

@pygics.service('GET', '/get/get')
def get2(req):
    print('get2')
    print(req)
    return {'test' : 'ok'}

@pygics.service('GET', '/get/get/get')
def get3(req, ext=None, a='a', b='b'):
    print('get3')
    print(req)
    print ext, a, b
    return {'test' : 'ok'}

@pygics.service('POST', '/post')
def post(req):
    print(req)
    return {'test' : 'ok'}

@pygics.service('PUT', '/put')
def put(req):
    print(req)
    return {'test' : 'ok'}

@pygics.service('DELETE', '/del')
def delete(req):
    print(req)
    return {'test' : 'ok'}

@pygics.service('GET', '/sum')
def sum(req, a, b):
    a = int(a)
    b = int(b)
    print('run sum : %d + %d = %d' % (a, b, a + b)) 
    return {'result' : a + b}

@pygics.service('GET', '/mul')
def mul(req, a, b):
    a = int(a)
    b = int(b)
    print('run mul : %d * %d = %d' % (a, b, a * b)) 
    return {'result' : a * b}

pygics.server(('0.0.0.0', 80))