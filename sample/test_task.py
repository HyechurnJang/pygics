# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 31.
@author: HyechurnJang
'''

from pygics import Queue, Lock, Task, sleep

#===============================================================================
# Queue Test
#===============================================================================
print 'Queue Test'
queue = Queue()
print 'PUT :', queue.put('queuing 1')
print 'PUT :', queue.put('queuing 2', block=False)
print 'GET :', queue.get()
print 'GET :', queue.get(block=False)

#===============================================================================
# Lock Test
#===============================================================================
print 'Lock Test'
lock = Lock()
print 'ON  :', lock.on()
print 'ON  :', lock.on(block=False)
print 'OFF :', lock.off()
print 'OFF :', lock.off()

#===============================================================================
# Task Test
#===============================================================================
print 'Task Test'
class TestTask(Task):
    
    def __init__(self, name, tick, delay):
        Task.__init__(self, tick, delay)
        self.name = name
        self.start()
        
    def __run__(self):
        print self.name

t1 = TestTask('Task1', 2, 1)
t2 = TestTask('Task2', 3, 2)

sleep(10)

t2.stop()
print 'Stop : t2'

sleep(5)

t1.stop()
print 'Stop : t1'

print 'Do Idle'
Task.idle()