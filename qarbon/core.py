# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Model core module."""

__all__ = ["Quality", "Access", "DisplayLevel", "DataAccess", "DataType", 
           "State", "Manager", "Factory", "Device", "Attribute"]

import abc
import sys
import weakref
import datetime

from qarbon.external.enum import Enum

from . import log
from .util import isString
from .signal import Signal

_PY3 = sys.version_info[0] > 2

ErrorStr = ErrorRepr = "Error!"

class Quality(Enum):
    Valid, \
    Invalid, \
    Alarm, \
    Changing, \
    Warning, \
    _Invalid = range(6)


class Access(Enum):
    Read, \
    ReadWithWrite, \
    Write, \
    ReadWrite, \
    _Invalid = range(5)


class DisplayLevel(Enum):
    Operator, \
    Expert, \
    Developer, \
    Administrator, \
    _Invalid = range(5)


class DataAccess(Enum):
    """Data access enum"""

    ReadOnly, ReadWithWrite, WriteOnly, ReadWrite, _Invalid = range(5)


class DataType(Enum):
    """Data type enum"""

    Integer, Float, String, Boolean, State, Enumeration, \
      Binary, _Invalid = range(8)

    #: dictionary dict<data type, :class:`DataType`>
    __DTYPE_MAP = {
        'int':         Integer,
        'integer':     Integer,
        int:           Integer,
        'long':        Integer,
        Integer:       Integer,
        'float':       Float,
        'double':      Float,
        float:         Float,
        Float:         Float,
        'str':         String,
        'string':      String,
        str:           String,
        String:        String,
        'bool':        Boolean,
        'boolean':     Boolean,
        bool:          Boolean,
        Boolean:       Boolean,
        'state':       State,
        State:         State,
        'enum':        Enumeration,
        'enumeration': Enumeration,
        Enumeration:   Enumeration,
        'bin':         Binary,
        'binary':      Binary,
        'bytes':       Binary,
        Binary:        Binary,
    }

    if _PY3:
        __DTYPE_MAP[bytes] = Binary
    else:
        __DTYPE_MAP[long] = Integer

    __PYTYPE_MAP = {
        Integer:     int,
        Float:       float,
        String:      str,
        Boolean:     bool,
        State:       State,
        Enumeration: Enum,
        Binary:      bytes
    }

    @staticmethod
    def toPythonType(dtype):
        """Convert from DataType to python type"""
        dtype = DataType.toDataType(dtype)
        return DataType.__PYTYPE_MAP[dtype]

    @staticmethod
    def toDataType(dtype):
        """Convert from type to DataType"""
        if isString(dtype):
            dtype = dtype.lower()
        return DataType.__DTYPE_MAP[dtype]


class State(Enum):
    """State enum"""
    # On, Moving, Fault, Alarm, Unknown, _Invalid = range(6)

    On, Off, Close, Open, Insert, Extract, Moving, Standby, Fault, Init, \
    Running, Alarm, Disable, Unknown, Disconnected, _Invalid = range(16)


class _Manager(object):
    
    def __init__(self):
        pass

    def get_device(self):
        pass

    def get_plugin(self):
        pass

    def register_plugin(self):
        pass


__MANAGER = _Manager()
def Manager():
    return __MANAGER


class BaseObject(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, parent=None):
        self.__name = name
        self.__parent = parent
        self.__children = weakref.WeakValueDictionary()

    @property
    def name(self):
        return self.__name

    def get_parent(self):
        return self.__parent

    def get_children(self):
        return self.__children
    
    def get_child(self, name):
        return self.__children.get(name)
    
    def has_child(self, name):
        return name in self.__children

    def add_child(self, name, child):
        self.__children[name] = child
        return child

     # -- simpler repr and str ------------------------------------------------
#    def __repr__(self):
#        cname, name = self.__class__.__name__, self.__name
#        return "{0}(name={1})".format(cname, name)

#    def __str__(self):
#        cname, name = self.__class__.__name__, self.__name
#        return "{0}({1})".format(cname, name)

    # -- more complete repr and str -------------------------------------------
    def __repr__(self):
       cname, parent, name = self.__class__.__name__, self.__parent, self.__name
       if parent is None:
           return "{0}(name={1})".format(cname, name)
       return "{0}(name={1}, parent={2!r})".format(cname, name, parent)
 
    def __str__(self):
       cname, parent, name = self.__class__.__name__, self.__parent, self.__name
       if parent is None:
           return "{0}({1})".format(cname, name)
       return "{0}({1}, {2})".format(cname, name, parent)


class Factory(BaseObject):

    schemes = ()

    def __init__(self, name=None, parent=None):
        if name is None:
            name = self.__class__.__name__
        BaseObject.__init__(self, name, parent=parent)

    @abc.abstractmethod
    def get_database(self, name):
        pass

    @abc.abstractmethod
    def get_device(self, name):
        pass

    @abc.abstractmethod
    def get_attribute(self, name):
        pass


class Database(BaseObject):

    def __init__(self, name, parent=None):
        BaseObject.__init__(self, name, parent=parent)

    @abc.abstractmethod
    def get_device(self, device_name):
        pass


class Device(BaseObject):

    def __init__(self, name, parent=None):
        BaseObject.__init__(self, name, parent=parent)

    @property
    def database(self):
        return self.get_parent()

    @abc.abstractmethod
    def get_attribute(self, attr_name):
        pass

    @abc.abstractmethod
    def execute(self, cmd, *args, **kwargs):
        pass


class Attribute(BaseObject):

    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        BaseObject.__init__(self, name, parent=parent)

    @property
    def device(self):
        return self.get_parent()

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def write(self, value):
        pass

