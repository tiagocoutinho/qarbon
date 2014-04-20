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
           "State", "Manager", "Factory", "Device", "Attribute",
           "AttributeConfig", "AttributeValue",
           "NullAttributeConfig", "NullAttributeValue"]

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


class AttributeConfig(object):
    
#    def __init__(self):
#        self.name = None
#        self.label = None
#        self.description = None
#        self.ndim = None
#        self.format = None
#        self.display_level = None
#        self.display_format = None
#        self.access = None
#        self.unit = None
#        self.standard_unit = None
#        self.display_unit = None
#        self.min_value = None
#        self.max_value = None
#        self.min_alarm = None
#        self.max_alarm = None
#        self.min_warning = None
#        self.max_warning = None
#        self.value_range = None, None
#        self.alarm_range = None, None
#        self.warning_range = None, None

#    def __init__(self):
#        self.name = ""
#        self.label = "-----"
#        self.description = ""
#        self.ndim = 0
#        self.format = "%s"
#        self.display_level = DisplayLevel._Invalid
#        self.display_format = "!s"
#        self.access = Access._Invalid
#        self.unit = None
#        self.standard_unit = None
#        self.display_unit = None
#        self.min_value = None
#        self.max_value = None
#        self.min_alarm = None
#        self.max_alarm = None
#        self.min_warning = None
#        self.max_warning = None
#        self.value_range = None, None
#        self.alarm_range = None, None
#        self.warning_range = None, None

    name = ""
    label = "-----"
    description = ""
    ndim = -1
    format = "%s"
    display_level = DisplayLevel._Invalid
    display_format = "!s"
    access = Access._Invalid
    unit = None
    standard_unit = None
    display_unit = None
    min_value = None
    max_value = None
    min_alarm = None
    max_alarm = None
    min_warning = None
    max_warning = None
    value_range = None, None
    alarm_range = None, None
    warning_range = None, None

    def is_write(self):
        return self.access == Access.Write

    def is_readonly(self):
        return self.access == Access.Read

    def is_readwrite(self):
        return self.access == Access.ReadWrite

    def is_scalar(self):
        return self.ndim == 0

    def is_spectrum(self):
        return self.ndim == 1

    def is_mage(self):
        return self.ndim == 2


NullAttributeConfig = AttributeConfig


class AttributeValue(object):
    """A qarbon value. A container for a value read from a qarbon model. It
    contains the following members:
    
    * r_value (Quantity): (aka: value) a Quantity representing the read value
    * r_timestamp (datetime.datetime): the timestamp of reading the value
    * w_value (Quantity): a Quantity representing the write value
    * quality (Quality): the quality related to the read value
    * exc_info (tuple): a 3-tuple equivalent to sys.exc_info() if reading a
                        value resulted in an exception or None otherwise
    * error (bool): tells the read resulted in an error
    * config (AttributeConfig): config object from which this value was obtained

    Other configuration values can also be accessed:

    * name (str): model name from which the value was obtained 
    * min_value (Quantity): minimum value allowed
    * max_value (Quantity): maximum value allowed
    * min_alarm (Quantity): minimum alarm value trigger
    * max_alarm (Quantity): maximum alarm value trigger
    * min_warning (Quantity): minimum warning value trigger
    * max_warning (Quantity): maximum warning value trigger
    * description (str): a description
    

    Example on how to pretty print 

    """

    r_value = None

    r_timestamp = None
    
    r_ndim = None

    r_quality = None

    w_value = None

    exc_info = None

    config = NullAttributeConfig

    def __getattr__(self, name):
        return getattr(self.config, name)

    def __str__(self):
        if self.error:
            value = ErrorStr
        else:
            value = self.r_value
        return "{0}".format(value)

    def __repr__(self):
        cname = self.__class__.__name__
        if self.error:
            value = ErrorRepr
        else:
            value = self.r_value
        return "{0}({1}, {2!r})".format(cname, self.name, self.r_value)
    
    def __format__(self, format_spec):
        if self.error:
            v = ErrorStr
        else:
            v = format(self.r_value, format_spec)
        return '{obj.label}: {0}'.format(v, obj=self)

    def __pformat__(self):
        return """\
AttributeValue
         name = {0.name}
        label = {0.label}
       access = {0.access}
display_level = {0.display_level}
         unit = {0.unit}
  value_range = {0.value_range}
  alarm_range = {0.alarm_range}
warning_range = {0.warning_range}
         ndim = {0.ndim}
      r_value = {0.r_value}
  r_timestamp = {0.r_timestamp}
    r_quality = {0.r_quality}
      w_value = {0.w_value}
        error = {0.error}
""".format(self)

    @property
    def value(self):
        return self.r_value

    @property
    def timestamp(self):
        return self.r_timestamp
    
    @property
    def ndim(self):
        return self.r_ndim

    @property
    def quality(self):
        return self.r_quality

    @property
    def error(self):
        return self.exc_info is not None

    def is_scalar(self):
        return self.ndim == 0

    def is_spectrum(self):
        return self.ndim == 1

    def is_image(self):
        return self.ndim == 2


NullAttributeValue = AttributeValue


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

