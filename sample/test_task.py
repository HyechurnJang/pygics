# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 31.
@author: HyechurnJang
'''

import pygics

class TestTask(pygics.Task):
    
    def __init__(self, name, tick, delay):
        pygics.Task.__init__(self, tick, delay)
        self.name = name
        self.start()
        
    def run(self):
        print self.name

t1 = TestTask('Task1', 2, 1)
t2 = TestTask('Task2', 3, 2)

for _ in range(0, 10):
    print 'Running Task : t1, t2'
    pygics.Time.sleep(1)

t2.stop()

for i in range(0, 5):
    print 'Running Task : t1'
    pygics.Time.sleep(1)

t1.stop()

for i in range(0, 2):
    print 'Running Task : Empty'
    pygics.Time.sleep(1)
