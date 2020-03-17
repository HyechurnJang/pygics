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

from pygics import Database, Table, Schema, sdk, dumpJson


# "PygicsDB" is database name
@sdk
class PygicsDB(Database):
    
    def __init__(self):
        Database.__init__(self, 'postgres')


# "User" is table name
# Schema definition based on SQLAlchemy
# more info at https://docs.sqlalchemy.org
# "SDK" is pre-defined keyword
@SDK.PygicsDB
class User(Table):
    
    # Column definition
    __schema__ = [
        Schema.Column('id', Schema.Integer, primary_key=True),
        Schema.Column('name', Schema.String),
        Schema.Column('fullname', Schema.String),
        Schema.Column('nickname', Schema.String)
    ]
    
    def __init__(self, name, fullname, nickname):
        Table.__init__(self, name=name, fullname=fullname, nickname=nickname)
    
    def __repr__(self, *args, **kwargs):
        return dumpJson({
            'ID' : self.id,
            'Name' : self.name,
            'FullName' : self.fullname,
            'NickName' : self.nickname
        }, indent=2)
