'''
Created on 2017. 1. 24.

@author: Hye-Churn Jang
'''

import gevent.lock
import gevent.queue
from jzlib import LifeCycle, kill
from .task_impl import TaskImpl, BurstImpl

def sleep(sec): gevent.sleep(sec)

def ctxchange(): gevent.sleep(0)
    
class Queue(LifeCycle, gevent.queue.Queue):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, *argv, **kargs): gevent.queue.Queue.__init__(self, *argv, **kargs)
    
    def __release__(self):
        while not self.empty(): kill(self.get())
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def put(self, item, block=True, timeout=None): gevent.queue.Queue.put(self, item, block=block, timeout=timeout)
    
    def get(self, block=True, timeout=None): return gevent.queue.Queue.get(self, block=block, timeout=timeout)

class Lock(LifeCycle, gevent.lock.Semaphore):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, *argv, **kargs): gevent.lock.Semaphore.__init__(self, *argv, **kargs)
    
    def __release__(self): self.off()
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def on(self, block=True, timeout=None): return gevent.lock.Semaphore.acquire(self, block, timeout)
    
    def off(self): return True if gevent.lock.Semaphore.release(self) > 0 else False
        
class Task(LifeCycle, TaskImpl):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, tick=0, delay=0, debug=False): TaskImpl.__init__(self, tick, delay, debug)
    
    def __release__(self): TaskImpl.stop(self)
    
    #===========================================================================
    # Implementations
    #===========================================================================
    def __run__(self): pass
    
    #===========================================================================
    # Class Methods
    #===========================================================================
    @classmethod
    def idle(cls): TaskImpl.idle()
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def start(self): return TaskImpl.start(self)
    
    def stop(self): return TaskImpl.stop(self)
    
    def isRun(self): return TaskImpl.isRun(self)
    
#===============================================================================
# Concurrent Tasking
#===============================================================================
class Burst(LifeCycle, BurstImpl):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, debug=False): BurstImpl.__init__(self, debug)
    
    def __release__(self): BurstImpl.kill(self)
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def __call__(self, method, *argv, **kargs): return BurstImpl.register(self, method, *argv, **kargs)
    
    def register(self, method, *argv, **kargs): return BurstImpl.register(self, method, *argv, **kargs)
    
    def do(self): return BurstImpl.do(self)
