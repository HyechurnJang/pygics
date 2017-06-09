# -*- coding: utf-8 -*-
'''
Created on 2017. 6. 9.
@author: HyechurnJang
'''

class __PYGICS__(object):
    
    def __release__(self): pass
        
    def __pygics_inspect_release__(self):
        if not hasattr(self, '__pygics_released__'):
            self.__pygics_released__ = True
            self.__release__()
    
    def __del__(self):
        self.__pygics_inspect_release__()
        