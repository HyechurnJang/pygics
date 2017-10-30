# -*- coding: utf-8 -*-
'''
Created on 2017. 10. 30.
@author: HyechurnJang
'''

import os
import re
import time
import shutil
import zipfile
import requests
from jzlib import modup, moddown

#===============================================================================
# Internal Module Management
#===============================================================================
def __remove_module_file__(name):
    mod_path = '%s/%s' % (ENV.DIR.MOD, name)
    if os.path.exists(mod_path) and os.path.isdir(mod_path):
        shutil.rmtree(mod_path)
        return True
    return False

def __unlink_module__(name):
    if name in ENV.EXPORT:
        ENV.EXPORT.pop(name)
        ENV.LOG.MODULE.info('delete api /%s/*' % name)
    moddown(name)

def __link_module__(path):
    modup(path)

def __install_dependency__(path):
    path = path + '/dependency.txt'
    if os.path.exists(path):
        with open(path) as fd: modules = fd.readlines()
        span = []
        for module in modules:
            rq = re.match('\s*(?P<module>[\w\.\-\:]+)', module)
            if rq != None: span.append(rq.group('module'))
        modules = span
        for module in modules: __install_module__(module)
        return modules
    return []
    
def __uninstall_module__(name):
    if name not in ENV.MOD.PRIO: raise Exception('could not find module %s' % name)
    __unlink_module__(name)
    ENV.MOD.PRIO.remove(name)
    if name in ENV.MOD.DESC: ENV.MOD.DESC.pop(name)
    ENV.MOD.save()
    __remove_module_file__(name)

def __install_module__(path):
    if re.search('^sys::', path):
        os_desc = path.split('::')
        os_type = os_desc[1].lower()
        os_dist = os_desc[2] if len(os_desc) > 2 else None
        os_ver = os_desc[3] if len(os_desc) > 3 else None
        if os_type != ENV.SYS.OS: raise Exception('could not support operation system')
        elif os_dist != None and os_dist != ENV.SYS.DIST: raise Exception('could not support operation system')
        elif os_ver != None and os_ver != ENV.SYS.VER: raise Exception('could not support operation system')
        print('system %s is matched' % path)
    elif re.search('^pkg::', path):
        package = path.replace('pkg::', '')
        if ENV.SYS.DIST in ['centos', 'redhat', 'fedora']: syscmd = 'yum install -q -y %s'
        elif ENV.SYS.DIST in ['ubuntu', 'debian']: syscmd = 'apt-get install -q -y %s'
        else: raise Exception('could not support installing system package')
        if os.system(syscmd % package) != 0: raise Exception('could not install system package %s' % path)
        print('system package %s is installed' % path)
    elif re.search('^pip::', path):
        if os.system('pip install -q %s' % path.replace('pip::', '')) != 0: raise Exception('could not install %s' % path)
        print('package %s is installed' % path)
    elif re.search('^(mod|app|exp)::', path):
        repo_desc = path.split('::')
        repo = repo_desc[0]
        name = repo_desc[1]
        branch = repo_desc[2] if len(repo_desc) > 2 else 'master'
        if name in ENV.MOD.PRIO: return
        mod_path = '%s/%s' % (ENV.DIR.MOD, name)
        if os.path.exists(mod_path) and os.path.isdir(mod_path):
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
        else:
            gzip_path = '%s.zip' % mod_path
            uzip_path = '%s/%s-%s' % (mod_path, name, branch)
            move_path = '%s/%s-%s' % (ENV.DIR.MOD, name, branch)
            if repo == 'mod': resp = requests.get('https://github.com/pygics-mod/%s/archive/%s.zip' % (name, branch))
            elif repo == 'app': resp = requests.get('https://github.com/pygics-app/%s/archive/%s.zip' % (name, branch))
            elif repo == 'exp': resp = requests.get('https://github.com/pygics-exp/%s/archive/%s.zip' % (name, branch))
            else: raise Exception('incorrect repository name %s' % repo)
            if resp.status_code != 200: raise Exception('could not find %s' % path)
            with open(gzip_path, 'wb') as fd: fd.write(resp.content)
            with zipfile.ZipFile(gzip_path, 'r') as fd: fd.extractall(mod_path)
            os.remove(gzip_path)
            shutil.move(uzip_path, ENV.DIR.MOD)
            shutil.rmtree(mod_path)
            os.rename(move_path, mod_path)
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
        ENV.MOD.DESC[name] = {'path' : path, 'base' : repo, 'name' : name, 'dist' : branch, 'deps' : deps, 'time' : time.strftime('%Y-%m-%d %X', time.localtime())}
        ENV.MOD.PRIO.append(name)
        ENV.MOD.save()
        print('module %s is installed' % path)
    else:
        if not os.path.exists(path): raise Exception('incorrect module path %s' % path)
        parent, name = os.path.split(path)
        name, ext = os.path.splitext(name)
        if zipfile.is_zipfile(path):
            mod_path = '%s/%s' % (ENV.DIR.MOD, name)
            if name in ENV.MOD.PRIO: __unlink_module__(name)
            __remove_module_file__(name)
            with zipfile.ZipFile(path, 'r') as fd: fd.extractall(mod_path)
            os.remove(path)
            deps = __install_dependency__(mod_path)
            __link_module__(mod_path)
            path = mod_path
        elif os.path.isdir(path):
            if name in ENV.MOD.PRIO: return
            deps = __install_dependency__(path)
            __link_module__(path)
        elif os.path.isfile(path):
            if ext == '.py':
                if name in ENV.MOD.PRIO: return
                deps = []
                __link_module__('%s/%s' % (parent, name))
            elif ext == '.raw':
                mod_path = '%s/%s' % (ENV.DIR.MOD, name)
                mod_init = '%s/__init__.py' % mod_path
                deps = []
                if name in ENV.MOD.PRIO: __unlink_module__(name)
                __remove_module_file__(name)
                os.mkdir(mod_path)
                shutil.move(path, mod_init)
                __link_module__(mod_path)
                path = mod_path
            else: raise Exception('could not install %s' % path)
        else: raise Exception('could not install %s' % path)
        if name not in ENV.MOD.PRIO: ENV.MOD.PRIO.append(name)
        ENV.MOD.DESC[name] = {'path' : path, 'base' : 'local module', 'name' : name, 'dist' : None, 'deps' : deps, 'time' : time.strftime('%Y-%m-%d %X', time.localtime())}
        ENV.MOD.save()
        print('module %s is installed' % path)