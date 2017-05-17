# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 30.
@author: HyechurnJang
'''

import pygics

# if "rest_module1.py" upload to pygics.service with named "rest_module1"
import rest_module1

#===============================================================================
# PYGICS TASK
#===============================================================================
class ModuleTask(pygics.Task):
    
    def __init__(self):
        pygics.Task.__init__(self, tick=1)
        self.start()
    
    def run(self):
        print('Run Module 2')
        rest_module1.internal_function('rest_module2')

# "pygics.Task" in "pygics.service" environment must be save object to variable
# if do not save object to variable, it don't stop with deleting module
task = ModuleTask()

#===============================================================================
# REST FUNCTION
#===============================================================================
# GET:<HOST>/<MODULE NAME>/function ----> 200 OK >> {"result" : "ok"}
@pygics.api('GET', '/function')
def module_function(req, *args, **kargs):
    return 'ok'
