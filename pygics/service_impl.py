# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 20.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import os
import re
import shutil
import zipfile
import requests

from jzlib import loadModule, unloadModule

def installDep(path):    
    path = path + '/dependency.txt'
    if os.path.exists(path):
        with open(path) as fd: modules = fd.readlines()
        for module in modules: pygics_install_module(module)

def installYum(path):
    kv = re.match('^yum::(?P<name>[\w\.\-]+)', path)
    if not kv: raise Exception('incorrect path %s' % path)
    name = kv.group('name')
    if ENV.SYS.DIST in ['centos', 'redhat', 'fedora']:
        if os.system('yum install -q -y %s' % name) != 0: raise Exception('could not install yum package %s' % name)
        print('yum package %s is installed' % name)
        ENV.MOD.register(path, 'yum', name, '')
    return []

def installApt(path):
    kv = re.match('^apt::(?P<name>[\w\.\-]+)', path)
    if not kv: raise Exception('incorrect path %s' % path)
    name = kv.group('name')
    if ENV.SYS.DIST in ['ubuntu', 'debian']:
        if os.system('apt install -q -y %s' % name) != 0: raise Exception('could not install apt package %s' % name)
        print('apt package %s is installed' % name)
        ENV.MOD.register(path, 'apt', name, '')

def installPip(path):
    kv = re.match('^pip::(?P<name>[\w\.\-]+)', path)
    if not kv: raise Exception('incorrect path %s' % path)
    name = kv.group('name')
    if os.system('pip install -q %s' % name) != 0: raise Exception('could not install pip package %s' % name)
    print('pip package %s is installed' % name)
    ENV.MOD.register(path, 'pip', name, '')

def installRepo(path):
    kv = re.match('^(?P<repo>(mod|app|exp))::(?P<name>[\w\.\-]+)(::(?P<branch>[\w\.\-]+))?', path)
    if not kv: raise Exception('incorrect path %s' % path)
    repo = kv.group('repo')
    name = kv.group('name')
    branch = kv.group('branch') if kv.group('branch') else 'master'
    fs_path = '%s/%s' %(ENV.DIR.MOD, name)
    if not os.path.exists(fs_path) or not os.path.isdir(fs_path):
        gzip_path = '%s-%s.zip' % (fs_path, branch)
        uzip_path = '%s-%s' % (fs_path, branch)
        code_path = '%s-%s/%s-%s' % (fs_path, branch, name, branch)
        resp = requests.get('https://github.com/pygics-%s/%s/archive/%s.zip' % (repo, name, branch))
        if resp.status_code != 200: raise Exception('could not find %s' % path)
        with open(gzip_path, 'wb') as fd: fd.write(resp.content)
        with zipfile.ZipFile(gzip_path, 'r') as fd: fd.extractall(uzip_path)
        shutil.move(code_path, fs_path)
        os.remove(gzip_path)
        shutil.rmtree(uzip_path)
    installDep(fs_path)
    loadModule(fs_path)
    ENV.MOD.register(path, repo, name, branch)
    print('repository %s is installed' % path)

def installZip(path):
    gzip_path = path.replace('zip::', '')
    if not zipfile.is_zipfile(gzip_path): raise Exception('incorrect path %s' % path)
    name = os.path.splitext(os.path.split(gzip_path)[1])[0]
    fs_path = '%s/%s' % (ENV.DIR.MOD, name)
    if os.path.exists(fs_path): shutil.rmtree(fs_path, ignore_errors=True)
    with zipfile.ZipFile(gzip_path, 'r') as fd: fd.extractall(ENV.DIR.MOD)
    installDep(fs_path)
    loadModule(fs_path)
    ENV.MOD.register(path, 'zip', name, '')
    print('zip archive %s is installed' % path)

def installDir(path):
    fs_path = path.replace('dir::', '')
    if not os.path.exists(fs_path) or not os.path.isdir(fs_path): raise Exception('incorrect path %s' % path)
    name = os.path.split(fs_path)[1]
    installDep(fs_path)
    loadModule(fs_path)
    ENV.MOD.register(path, 'dir', name, '')
    print('directory %s is installed' % path)

def installPy(path):
    fs_path = path.replace('py::', '')
    if not os.path.exists(fs_path) or not os.path.isfile(fs_path): raise Exception('incorrect path %s' % path)
    name = os.path.splitext(os.path.split(fs_path)[1])[0]
    loadModule(fs_path)
    ENV.MOD.register(path, 'py', name, '')
    print('py file %s is installed' % path)

def installPath(path):
    if not os.path.exists(path): raise Exception('incorrect path %s' % path)
    if os.path.isdir(path): installDir('dir::' + path)
    elif os.path.isfile(path): installPy('py::' + path)
