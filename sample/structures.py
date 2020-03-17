# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 3. 17..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

from pygics import Inventory, singleton, logInfo


#===============================================================================
# Simple Singleton
#===============================================================================
@singleton
class OnlyOne:
    
    def introduce(self):
        logInfo('This is Instance Method')


# OnlyOne keyword is Singleton Instance
OnlyOne.introduce()


#===============================================================================
# Customized Singleton
#===============================================================================
@singleton('MyBox', owner='OASIS', st_namespace='MyCategory', st_name='SecretBox')
class Box:
    
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
    
    def introduce(self):
        logInfo("This is {}'s {}".format(self.owner, self.name))


# MyCategory.SecretBox keyword is Singleton Instance
MyCategory.SecretBox.introduce()


#===============================================================================
# Inventory
#===============================================================================
class DataCenter(Inventory):
    
    class ClusterA(Inventory):
        
        def introduce(self):
            logInfo('Cluster A')
        
        class Host1(Inventory):
            
            def introduce(self):
                logInfo('Host 1')
        
        class Host2(Inventory):
            
            def introduce(self):
                logInfo('Host 2')
    
    class ClusterB(Inventory):
        
        def introduce(self):
            logInfo('Cluster A')
    
    def __init__(self):
        Inventory.__init__(self)  # Inventory.__init__ must be only run on Root Inventory
    
    def introduce(self):
        logInfo('DataCenter')


class Host3(Inventory):
    
    def introduce(self):
        logInfo('Host 3')


DC = DataCenter()
DC.ClusterA.Host1.introduce()
host1 = DC.ClusterA.Host1
(-host1).introduce()  # point to Parent Inventory
(- -host1).introduce()  # point to Parent's Parent Inventory
(~host1).introduce()  # point to Root Inventory
Host3().setParent(DC.ClusterB)  # Insert Host3 into DC.ClusterB Inventory
DC.ClusterB.Host3.introduce()
    
