# -*- coding: utf-8 -*-
'''
Created on 2018. 10. 10.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import sys
import pygics

pygics.environment('/pygics')
pygics.server('0.0.0.0', 80, *sys.argv[1:])