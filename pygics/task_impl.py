# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 20.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import time
import gevent

class TaskImpl:
    
    @classmethod
    def idle(cls):
        
        class IdleTask(TaskImpl):
            def __init__(self):
                TaskImpl.__init__(self, tick=31557600, delay=31557600, debug=False)
                self.start()
                
        task = IdleTask()
        while task.isRun(): gevent.sleep(31557600) 
    
    def __init__(self, tick, delay, debug):
        self._pygics_task = None
        self._pygics_task_sw = False
        self._pygics_task_tick = tick
        self._pygics_task_delay = delay
        self._pygics_task_debug = debug
    
    def __thread_wrapper__(self):
        if self._pygics_task_delay > 0: gevent.sleep(self._pygics_task_delay)
        while self._pygics_task_sw:
            if self._pygics_task_tick > 0:
                start_time = time.time()
                try: self.__run__()
                except Exception as e:
                    if self._pygics_task_debug: print('[Error]Task>>%s' % str(e))
                end_time = time.time()
                sleep_time = self._pygics_task_tick - (end_time - start_time)
                if sleep_time > 0: gevent.sleep(sleep_time)
                else:
                    if self._pygics_task_debug: print('[Warning]Task:Processing Time Over Tick')
                    gevent.sleep(0)
            else:
                try: self.__run__()
                except Exception as e:
                    if self._pygics_task_debug: print('[Error]Task>>%s' % str(e))
                gevent.sleep(0)
    
    def start(self):
        if not self._pygics_task:
            self._pygics_task_sw = True
            self._pygics_task = gevent.spawn(self.__thread_wrapper__)
        return self
    
    def stop(self):
        if self._pygics_task:
            self._pygics_task_sw = False
            gevent.kill(self._pygics_task)
            gevent.joinall([self._pygics_task])
            self._pygics_task = None
        return self
        
    def isRun(self):
        return self._pygics_task_sw

class BurstImpl:
    
    def __init__(self, debug):
        self._pygics_burst_fetches = []
        self._pygics_burst_methods = []
        self._pygics_burst_args = []
        self._pygics_burst_kargs = []
        self._pygics_burst_length = 0
        self._pygics_burst_debug = debug
    
    def register(self, method, *argv, **kargs):
        self._pygics_burst_methods.append(method)
        self._pygics_burst_args.append(argv)
        self._pygics_burst_kargs.append(kargs)
        self._pygics_burst_length += 1
        return self
    
    def kill(self):
        if self._pygics_burst_fetches:
            for fetch in self._pygics_burst_fetches: gevent.kill(fetch)
        return self
    
    def do(self):
        ret = [None for i in range(0, self._pygics_burst_length)]
        
        def fetch(_method, _ret, _index, *argv, **kargs):
            try: _ret[_index] = _method(*argv, **kargs)
            except Exception as e:
                if self._pygics_burst_debug: print('[Error]Burst>>%s' % str(e))
        
        for i in range(0, self._pygics_burst_length):
            self._pygics_burst_fetches.append(gevent.spawn(fetch,
                                                           self._pygics_burst_methods[i],
                                                           ret,
                                                           i,
                                                           *self._pygics_burst_args[i],
                                                           **self._pygics_burst_kargs[i]))
        
        gevent.joinall(self._pygics_burst_fetches)
        self._pygics_burst_fetches = []
        return ret