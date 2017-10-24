# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 3.

@author: Hye-Churn Jang
'''

from pygics import Burst, sleep

def getSum(a, b):
    sleep(4)
    return a + b

def getMul(a, b):
    sleep(2)
    return a * b

print Burst().register(getSum, 1, 1).register(getMul, 1, 1).do()
