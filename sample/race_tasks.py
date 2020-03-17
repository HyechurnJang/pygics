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
        Task.__init__(self, tick=1, delay=start_sec)  # every 1 sec run task
        self.name = name
        self.start()
    
    def __run__(self):
        lock.on()
        logInfo('{} run faster more than others.'.format(self.name))
        lock.off()
        repose()


class Ferrari(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Ferrari', 0)  # start after 0 sec


class Lamborghini(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Lamborghini', 2)  # start after 2 sec


class Porsche(SportsCar):
    
    def __init__(self):
        SportsCar.__init__(self, 'Porsche', 4)  # start after 4 sec


f = Ferrari()
l = Lamborghini()
p = Porsche()

sleep(6)
f.stop()  # stop Ferrari
sleep(3)
kill(l)  # kill Lamborghini
sleep(3)
p.stop()  # stop Porsche
