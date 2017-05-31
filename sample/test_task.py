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

pygics.Time.sleep(10)

t2.stop()
print 'Stop : t2'

pygics.Time.sleep(5)

t1.stop()
print 'Stop : t1'
