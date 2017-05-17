# -*- coding: utf-8 -*-
'''
Created on 2017. 4. 18.
@author: HyechurnJang
'''

import pygics

@pygics.model('testdb')
class TestModel:
    name = str
    id = int
    data = float

pygics.server('0.0.0.0', 80)
