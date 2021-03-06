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

from pygics import Model, RestUser, Rest, sdk, logInfo


#===============================================================================
# Definitions
#===============================================================================
# Define User Session Mechanism
class CalcUser(RestUser):
    
    def __headers__(self, **kwargs):
        #=======================================================================
        # Example User Session Creation by Bearer Token
        # 
        # RestUser.__headers__(self, **{
        #     'Accept': 'application/json',
        #     'Content-Type': 'application/json'
        # })
        # self.token = self.sdk.doPostMethod('/login', {'username' : self.username, 'password' : self.password}).json()['token']
        # RestUser.__headers__(self, Authorization='Bearer ' + self.token)
        #=======================================================================
        RestUser.__headers__(self)


# Define Client Mechanism
@sdk
class CalcSDK(Rest):
    
    def __init__(self):
        Rest.__init__(self, user_model=CalcUser)


# Define Rest API Model
# @SDK.CalcSDK.create
# @SDK.CalcSDK.list
# @SDK.CalcSDK.get
# @SDK.CalcSDK.update('put' or 'patch' or 'post')
# @SDK.CalcSDK.delete
# @SDK.CalcSDK.entry # Register Model to Client Attribute
@SDK.CalcSDK.list
@SDK.CalcSDK.get()  # "()" meaning is default calling is triggered "get" method
@SDK.CalcSDK(api='', url='/{historyId}', historyId='id', list_layer=['history'], layer=['result'])
class CalcHistory(Model): pass


#===============================================================================
# Sample Run
#===============================================================================
SDK.CalcSDK.system('http://localhost/api/calculator', 'admin', 'password')
user = SDK.CalcSDK.login('username', 'password')

# default is system session
for i in range(1, 3):
    logInfo(SDK.CalcSDK.doGetMethod('/add/{}/{}'.format(i, i * i)).json())  # Row Level Get

logInfo('History\n{}'.format(CalcHistory.list()))  # Get List of Rest API Model
logInfo('index=1 History\n{}'.format(CalcHistory.get('1')))  # Get One of Rest API Model

# user session transaction
with user:
    logInfo(SDK.CalcSDK.doPostMethod('/multi-add', [1, 3, 5]).json())  # Row Level Post
    logInfo(SDK.CalcSDK.doGetMethod('/sub?a=10&b=1').json())  # Row Level Get

# system session
logInfo('History\n{}'.format(CalcHistory.list()))

