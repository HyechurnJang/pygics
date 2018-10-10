# -*- coding: utf-8 -*-
'''
Created on 2018. 10. 10.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import pygics
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-p', '--port', help='Listen Port', required=True)
    parser.add_argument('-m', '--module', help='Import Modules', required=True)
    args = parser.parse_args()
    
    port = args.port
    if not port.isdigit(): raise Exception('port is not number')
    port = int(args.port)
    modules = args.module.split(',')
    modules = [ module.strip() for module in modules ]
    
    pygics.server('0.0.0.0', port, *modules)
