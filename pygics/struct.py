# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 2. 15.
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

from inspect import isclass, getmro
from .common import logDebug


class PygObj(object):
    
    #===========================================================================
    # Interface Method : To be re-written
    #===========================================================================
    def __kill__(self):
        ### distruction logic here ###
        pass
    
    #===========================================================================
    # System Methods
    #===========================================================================
    def __pygobj_kill__(self):
        if not hasattr(self, '_pygobj_killed'):
            self._pygobj_killed = True
            self.__kill__()
    
    def __del__(self):
        self.__pygobj_kill__()


class Inventory(PygObj):
    
    #===========================================================================
    # Life Cycle Methods
    #===========================================================================
    def __init__(self, root=None, parent=None, tracking=True):
        if root != None: self._pyg_inventory_root = root
        else: self._pyg_inventory_root = self
        if parent != None: self._pyg_inventory_parent = parent
        else: self._pyg_inventory_parent = self
        self._pyg_inventory_children = {}
        if tracking:
            for mro in reversed(getmro(self.__class__)):
                if mro == object or mro == Inventory: continue
                elems = mro.__dict__
                for name, cls in elems.items():
                    if isclass(cls) and issubclass(cls, Inventory):
                        inst = cls()
                        Inventory.__init__(inst, self._pyg_inventory_root, self, tracking)
                        self.__setattr__(name, inst)
                        self._pyg_inventory_children[name] = inst
        self.__post_init__()
    
    def __post_init__(self): pass
    
    #===========================================================================
    # Operation Methods
    #===========================================================================
    def __invert__(self):
        return self._pyg_inventory_root

    def __neg__(self):
        return self._pyg_inventory_parent

    def __pos__(self):
        return self._pyg_inventory_children
    
    def setParent(self, parent, name=None, with_children=True):
        if isinstance(parent, Inventory):
            if not name: name = self.__class__.__name__
            self._pyg_inventory_root = parent._pyg_inventory_root
            self._pyg_inventory_parent = parent
            if not with_children:
                if name in parent._pyg_inventory_children:
                    self._pyg_inventory_children = parent._pyg_inventory_children[name]._pyg_inventory_children
            parent.__setattr__(name, self)
            parent._pyg_inventory_children[name] = self
        return self
    
    def setParentWithChildren(self, parent, name=None):
        return self.setParent(parent, name, with_children=True)
    
    def setParentWithOutChildren(self, parent, name=None):
        return self.setParent(parent, name, with_children=False)


def kill(obj):
    if isinstance(obj, PygObj):
        obj.__pygobj_kill__()
        logDebug('[Pygics Object] kill %s' % obj.__class__.__name__)
    del obj


def singleton(*args, **kwargs):
    
    class SingletonNamespace(object): pass
    
    def register(cls):
        cl_name = cls.__name__
        st_name = kwargs.pop('st_name') if 'st_name' in kwargs else cl_name
        st_namespace = kwargs.pop('st_namespace') if 'st_namespace' in kwargs else 'Pygics'
        if st_namespace not in __builtins__:
            __builtins__[st_namespace] = SingletonNamespace()
        if not hasattr(__builtins__[st_namespace], st_name):
            inst = cls(*args, **kwargs)
            __builtins__[st_namespace].__setattr__(st_name, inst)
            logDebug('[Pygics Singleton] create singleton %s > %s.%s' % (cl_name, st_namespace, st_name), bold=True)
        else:
            inst = __builtins__[st_namespace].__getattribute__(st_name)
        return inst
    
    if len(args) == 1 and isclass(args[0]):
        cls = args[0]
        args = []
        return register(cls)
    else:
        return register
