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

#===============================================================================
# Prepare PostgreSQL Server
#===============================================================================
# docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_USER=pygics -e POSTGRES_DB=pygicsdb -d postgres

from pygics import load, logInfo

load('modules.postgres')

# Login Database
SDK.PygicsDB.system('localhost:5432', 'pygics', 'password')
# "User" Table at "PygicsDB" Database
User = SDK.PygicsDB.User

logInfo('Create Users')
with SDK.PygicsDB:  # Open Transaction for Create Records
    User('Tony', 'Tony Stark', 'IronMan')
    User('Peter', 'Peter Parker', 'SpiderMan')
    User('Peter', 'Peter Pan', 'Elf')

logInfo('Get All Users\n{}'.format(User.list()))

# query form based SQLAlchemy
logInfo('Find All Peters\n{}'.format(User.list(User.name == 'Peter', order='id')))

with SDK.PygicsDB:  # Open Transaction
    tony = User.list(User.name == 'Tony')[0]
    tony.nickname = 'Avengers Leader'  # Update Data
    tony.update()
    
logInfo('Check Tony Changed\n{}'.format(User.list(User.name == 'Tony')))

logInfo('Delete All Users')
with SDK.PygicsDB:  # Open Transaction for Delete
    for user in User.list():
        user.delete()

logInfo('Check Users Empty\n{}'.format(User.list()))
