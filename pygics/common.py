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

import os
import sys
import json
import yaml
import datetime
import importlib
import traceback
from watchdog_gevent import Observer
from watchdog.events import FileSystemEventHandler

__builtins__['__PYG_LOG_LEVEL__'] = 3


class LogLevel:
    
    Debug = 4  # gt 3
    Info = 3  # gt 2
    Warn = 2  # gt 1
    Error = 1  # gt 0
    
    class LogType:
    
        Debug = 'Debug'
        Info = 'Info'
        Warn = 'Warning'
        Error = 'Error'
    
    @classmethod
    def setLogLevel(cls, level):
        __builtins__['__PYG_LOG_LEVEL__'] = level


def log(msg, level=LogLevel.LogType.Info, bold=False):
    lmsg = '%s' % level.upper() if bold else '%s' % level
    msg = '[%s] [%s] %s' % (datetime.datetime.now(), lmsg, msg)
    print(msg)


def logDebug(msg, bold=False):
    if __PYG_LOG_LEVEL__ > 3:
        log(msg, LogLevel.LogType.Debug, bold)


def logInfo(msg, bold=False):
    if __PYG_LOG_LEVEL__ > 2:
        log(msg, LogLevel.LogType.Info, bold)


def logWarn(msg, bold=False):
    if __PYG_LOG_LEVEL__ > 1:
        log(msg, LogLevel.LogType.Warn, bold)


def logError(msg, bold=True):
    if __PYG_LOG_LEVEL__ > 0:
        log(msg, LogLevel.LogType.Error, bold)


def setEnv(**kwargs):
    for k, v in kwargs.items(): __builtins__[k] = v


def setEnvObject(obj):
    try: setEnv(**{obj.__name__ : obj})
    except: raise Exception('could not register object')
    return obj


def loadJson(json_str):
    return json.loads(json_str)


def dumpJson(obj, indent=None, sort_keys=False):

    def json_default(val): return str(val)

    return json.dumps(obj, default=json_default, indent=indent, sort_keys=sort_keys)


def ppJson(obj):
    print(dumpJson(obj, indent=2))


def loadYaml(yaml_str):
    return yaml.safe_load(yaml_str)


def dumpYaml(obj):
    return yaml.dump(obj)


def load(path):
    
    class Handler(FileSystemEventHandler):
        
        def on_modified(self, event):
            path = __PYG_MODULES_BY_FILE__[event.src_path]
            try:
                mod = importlib.reload(__PYG_MODULES_BY_PATH__[path])
            except Exception as e:
                traceback.print_exc()
                logError('[Pygics Module] %s > %s' % (str(e), path))
                return
            __PYG_MODULES_BY_PATH__[path] = mod
            logDebug('[Pygics Module] Reload > %s' % path)
    
    class Watcher(Observer):
         
        def __init__(self):
            Observer.__init__(self)
            self._pyg_watcher_handler = Handler()
            self.start()
        
        def register(self, path):
            self.schedule(self._pyg_watcher_handler, path=path)
    
    try: __PYG_MODULES_BY_PATH__
    except:
        __builtins__['__PYG_MODULES_BY_PATH__'] = {}
        __builtins__['__PYG_MODULES_BY_FILE__'] = {}
        __builtins__['__PYG_MODULES_WATCHER__'] = Watcher()
    
    if path in __PYG_MODULES_BY_PATH__:
        return __PYG_MODULES_BY_PATH__[path]
    else:
        if os.path.exists(path):
            directory, name = os.path.split(path)
            py_path, _ = os.path.splitext(name)
            if dir not in ['', '.'] and dir not in sys.path: sys.path.insert(0, directory)
        else:
            py_path = path
        try:
            mod = importlib.import_module(py_path)
        except Exception as e:
            traceback.print_exc()
            logError('[Pygics Module] %s > %s' % (str(e), path))
            raise e
        fs_path = mod.__file__
        __PYG_MODULES_BY_PATH__[path] = mod
        __PYG_MODULES_BY_FILE__[fs_path] = path
        __PYG_MODULES_WATCHER__.register(fs_path)
        logDebug('[Pygics Module] Loaded > %s' % path)
        return mod
