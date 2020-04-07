# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 3. 18..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

from pygics import Client, logInfo, sdk


@sdk
class CalcClient(Client):
    
    def __init__(self):
        Client.__init__(self, 'localhost', 80, '/api/calculator')


for i in range(1, 3):
    logInfo(SDK.CalcClient.GET.add(i, i * i))  # GET /api/calculator/add/<i>/<i * i>

logInfo('History\n{}'.format(SDK.CalcClient.GET()))  # GET /api/calculator
logInfo('index=1 History\n{}'.format(SDK.CalcClient.GET('1')))  # GET /api/calculator/1
