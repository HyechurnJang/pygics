# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 3.

@author: Hye-Churn Jang
'''

import pygics

def getSum(a, b):
    pygics.Time.sleep(4)
    return a + b

def getMul(a, b):
    pygics.Time.sleep(2)
    return a * b

getSum_ret, getMul_ret = pygics.Burst().register(getSum, 1, 1).register(getMul, 1, 1).do()
print getSum_ret, getMul_ret
