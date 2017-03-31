# -*- coding: utf-8 -*-
'''
Created on 2017. 3. 3.

@author: Hye-Churn Jang
'''

import pygics

def getSum(a, b):
    for _ in range(0, 4):
        print a + b
        pygics.Time.sleep(1)
    return a + b

def getMul(a, b):
    for _ in range(0, 2):
        print a * b
        pygics.Time.sleep(1)
    return a * b

print pygics.Burst().register(getSum, 1, 1).register(getMul, 1, 1).do()
