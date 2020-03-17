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

import time
import traceback
import gevent
import gevent.lock
import gevent.queue
from .common import logWarn, logError
from .struct import PygObj, kill


class Queue(PygObj, gevent.queue.Queue):
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def put(self, item, block=True, timeout=None):
        gevent.queue.Queue.put(self, item, block=block, timeout=timeout)
    
    def get(self, block=True, timeout=None):
        return gevent.queue.Queue.get(self, block=block, timeout=timeout)
    
    def clean(self):
        while not self.empty(): kill(self.get())
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, *argv, **kargs):
        gevent.queue.Queue.__init__(self, *argv, **kargs)
    
    def __kill__(self):
        while not self.empty(): kill(self.get())


class Lock(PygObj, gevent.lock.Semaphore):
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def on(self, block=True, timeout=None):
        return gevent.lock.Semaphore.acquire(self, block, timeout)
    
    def off(self):
        return True if gevent.lock.Semaphore.release(self) > 0 else False
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, *argv, **kargs):
        gevent.lock.Semaphore.__init__(self, *argv, **kargs)
    
    def __kill__(self):
        self.off()

        
class Task(PygObj):
    
    #===========================================================================
    # Interface Method : To be re-written
    #===========================================================================
    def __run__(self): pass
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def start(self):
        if not self._pyg_task:
            self._pyg_task_sw = True
            self._pyg_task = gevent.spawn(self.__thread_wrapper__)
        return self
    
    def stop(self):
        if self._pyg_task:
            self._pyg_task_sw = False
            gevent.kill(self._pyg_task)
            gevent.joinall([self._pyg_task])
            self._pyg_task = None
        return self
    
    def isRun(self):
        return self._pyg_task_sw
    
    #===========================================================================
    # Class Methods
    #===========================================================================
    @classmethod
    def idle(cls):
        
        class IdleTask(Task):

            def __init__(self):
                Task.__init__(self, tick=31557600, delay=31557600)
                self.start()
                
        task = IdleTask()
        while task.isRun(): gevent.sleep(31557600)
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, tick=0, delay=0):
        self._pyg_task = None
        self._pyg_task_sw = False
        self._pyg_task_tick = tick
        self._pyg_task_delay = delay
    
    def __kill__(self):
        self.stop()
    
    #===========================================================================
    # Inner Management
    #===========================================================================
    def __thread_wrapper__(self):
        if self._pyg_task_delay > 0: gevent.sleep(self._pyg_task_delay)
        while self._pyg_task_sw:
            if self._pyg_task_tick > 0:
                start_time = time.time()
                try: self.__run__()
                except Exception as e:
                    traceback.print_exc()
                    logError('[Pygics Task] %s' % str(e))
                end_time = time.time()
                sleep_time = self._pyg_task_tick - (end_time - start_time)
                if sleep_time > 0: gevent.sleep(sleep_time)
                else:
                    logWarn('[Pygics Task] processing time over tick')
                    gevent.sleep(0)
            else:
                try: self.__run__()
                except Exception as e:
                    traceback.print_exc()
                    logError('[Pygics Task] %s' % str(e))
                    gevent.sleep(0)

    
#===============================================================================
# Concurrent Tasking
#===============================================================================
class Burst(PygObj):
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def __call__(self, method, *argv, **kargs):
        return self.register(self, method, *argv, **kargs)
    
    def register(self, method, *argv, **kargs):
        self._pyg_burst_methods.append(method)
        self._pyg_burst_args.append(argv)
        self._pyg_burst_kargs.append(kargs)
        return self
    
    def start(self):
        ret = [None for i in range(0, len(self._pyg_burst_methods))]
        
        def fetch(_method, _ret, _index, *argv, **kargs):
            try: _ret[_index] = _method(*argv, **kargs)
            except Exception as e:
                traceback.print_exc()
                logError('[Pygics Burst] %s' % str(e))
        
        for i in range(0, len(self._pyg_burst_methods)):
            self._pyg_burst_fetches.append(gevent.spawn(fetch,
                                                           self._pyg_burst_methods[i],
                                                           ret,
                                                           i,
                                                           *self._pyg_burst_args[i],
                                                           **self._pyg_burst_kargs[i]))
        
        gevent.joinall(self._pyg_burst_fetches)
        self._pyg_burst_fetches = []
        return ret
    
    def stop(self):
        if self._pyg_burst_fetches:
            for fetch in self._pyg_burst_fetches: gevent.kill(fetch)
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self):
        self._pyg_burst_fetches = []
        self._pyg_burst_methods = []
        self._pyg_burst_args = []
        self._pyg_burst_kargs = []
    
    def __kill__(self):
        self.stop()


def sleep(sec):
    gevent.sleep(sec)


def repose():
    gevent.sleep(0)
