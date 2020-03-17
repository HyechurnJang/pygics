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

from pygics import Task, Lock, sleep, repose, kill, logInfo


lock = Lock()

class SportsCar(Task):
    
    def __init__(self, name, start_sec):
        Task.__init__(self, tick=1, delay=start_sec)
        self.name = name
        self.start()
    
    def __run__(self):
        lock.on()
        logInfo('{} run faster more than others.'.format(self.name))
        lock.off()
        repose()

class Ferrari(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Ferrari', 0)

class Lamborghini(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Lamborghini', 2)

class Porsche(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Porsche', 4)

f = Ferrari()
l = Lamborghini()
p = Porsche()

sleep(6)
f.stop()
sleep(3)
kill(l)
sleep(3)
p.stop()
