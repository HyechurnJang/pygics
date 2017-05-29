# -*- coding: utf-8 -*-
'''
Created on 2017. 5. 16.
@author: HyechurnJang
'''

import pygics

pygics.server('0.0.0.0',
              80,
              resource={'root' : './',
                        'read' : True,
                        'write' : True})