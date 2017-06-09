'''
Created on 2017. 1. 24.

@author: Hye-Churn Jang
'''

import time
import gevent
import gevent.queue
import gevent.lock
from .core import __PYGICS__

#===============================================================================
# Tasking Utils
#===============================================================================
class Time:
    
    @classmethod
    def sleep(cls, sec): gevent.sleep(sec)
    
class Queue(__PYGICS__, gevent.queue.Queue):
    
    def __init__(self, *argv, **kargs):
        gevent.queue.Queue.__init__(self, *argv, **kargs)

class Lock(__PYGICS__, gevent.lock.Semaphore):
    
    def __init__(self, *argv, **kargs):
        gevent.lock.Semaphore.__init__(self, *argv, **kargs)

#===============================================================================
# Tasking
#===============================================================================
class Task(__PYGICS__):
    
    @classmethod
    def yielding(cls): gevent.sleep(0)
    
    def __init__(self, tick=0, delay=0, debug=False):
        self._pygics_thread = None
        self._pygics_thread_sw = False
        self._pygics_thread_tick = tick
        self._pygics_thread_delay = delay
        self._pygics_thread_debug = debug
    
    def __release__(self):
        self.stop()
    
    def __thread_wrapper__(self):
        if self._pygics_thread_delay > 0: Time.sleep(self._pygics_thread_delay)
        while self._pygics_thread_sw:
            if self._pygics_thread_tick > 0:
                start_time = time.time()
                try: self.run()
                except Exception as e:
                    if self._pygics_thread_debug: print('[Error]Task:%s' % str(e))
                end_time = time.time()
                sleep_time = self._pygics_thread_tick - (end_time - start_time)
                if sleep_time > 0: Time.sleep(sleep_time)
                else:
                    if self._pygics_thread_debug: print('[Warning]Task:Processing Time Over Tick')
                    Task.yielding()
            else:
                try: self.run()
                except Exception as e:
                    if self._pygics_thread_debug: print('[Error]Task:%s' % str(e))
                Task.yielding()
    
    def start(self):
        if self._pygics_thread == None:
            self._pygics_thread_sw = True
            self._pygics_thread = gevent.spawn(self.__thread_wrapper__)
        return self
    
    def stop(self):
        if self._pygics_thread != None:
            self._pygics_thread_sw = False
            gevent.kill(self._pygics_thread)
            gevent.joinall([self._pygics_thread])
            self._pygics_thread = None
        return self
        
    def run(self):
        pass
    
    def isRun(self):
        return self._pygics_thread_sw

#===============================================================================
# Concurrent Tasking
#===============================================================================
class Burst(__PYGICS__):
    
    def __init__(self, debug=False):
        self.methods = []
        self.args = []
        self.kargs = []
        self.length = 0
        self.debug = debug
    
    def register(self, method, *argv, **kargs):
        self.methods.append(method)
        self.args.append(argv)
        self.kargs.append(kargs)
        self.length += 1
        return self
    
    def __call__(self, method, *argv, **kargs):
        return self.register(method, *argv, **kargs)
    
    def do(self):
        ret = [None for i in range(0, self.length)]
        fetches = []
        
        def fetch(__method__, __ret__, __index__, *argv, **kargs):
            try: __ret__[__index__] = __method__(*argv, **kargs)
            except Exception as e:
                if self.debug: print('[Error]Burst:%s' % str(e))
        
        for i in range(0, self.length):
            fetches.append(gevent.spawn(fetch, self.methods[i], ret, i, *self.args[i], **self.kargs[i]))
        
        gevent.joinall(fetches)
        return ret
