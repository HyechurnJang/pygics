'''
Created on 2017. 1. 24.

@author: Hye-Churn Jang
'''

import time
import threading
try: from Queue import Queue
except: from queue import Queue

#===============================================================================
# Thread
#===============================================================================
class Thread:
    
    class ThreadWrapper(threading.Thread):
        
        def __init__(self, pt):
            threading.Thread.__init__(self)
            self.pt = pt
            self.sw = False
        
        def run(self):
            while self.sw: self.pt.thread()
    
    def __init__(self):
        self._pygics_thread = Thread.ThreadWrapper(self)
        
    def start(self):
        if not self._pygics_thread.sw:
            self._pygics_thread.sw = True
            self._pygics_thread.start()
    
    def stop(self):
        if self._pygics_thread.sw:
            self._pygics_thread.sw = False
            try: self._pygics_thread._Thread__stop()
            except:
                try: self._pygics_thread._stop()
                except:
                    try: self._pygics_thread.__stop()
                    except: pass
            self._pygics_thread.join()
        
    def thread(self): pass

#===============================================================================
# Scheduler
#===============================================================================
class Task:
    def __init__(self, tick):
        self._pygics_task_tick = tick
        self._pygics_task_cur = 0
        
    def __pygics_sched_wrapper__(self, tick):
        self._pygics_task_cur += tick
        if self._pygics_task_cur >= self._pygics_task_tick:
            self._pygics_task_cur = 0
            self.task()
            
    def task(self): pass

class Scheduler(Thread):
    
    def __init__(self, tick):
        Thread.__init__(self)
        self._pygics_sched_tick = tick
        self._pygics_sched_q = []
        self._pygics_sched_reg = Queue()
    
    def thread(self):
        start_time = time.time()
        while not self._pygics_sched_reg.empty():
            task = self._pygics_sched_reg.get()
            self._pygics_sched_q.append(task)
        for task in self._pygics_sched_q:
            try: task.__pygics_sched_wrapper__(self._pygics_sched_tick)
            except: continue
        end_time = time.time()
        sleep_time = self._pygics_sched_tick - (end_time - start_time)
        if sleep_time > 0: time.sleep(sleep_time)
            
    def register(self, task):
        self._pygics_sched_reg.put(task)
        
    def unregister(self, task):
        sw = self._pygics_thread.sw
        if sw: self.stop()
        if task in self._pygics_sched_q: self._pygics_sched_q.remove(task)
        if sw: self.start()
    