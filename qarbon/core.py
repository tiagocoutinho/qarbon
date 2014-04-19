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
           "State", "AttributeConfig", "AttributeValue", "Manager",
           "Factory", "Device", "Attribute", "Signal"]

import abc
import sys
import weakref
import datetime

from qarbon.external.enum import Enum

from . import log
from .util import isString, callable_weakref

_PY3 = sys.version_info[0] > 2

class Quality(Enum):
    Valid, \
    Invalid, \
    Alarm, \
    Changing, \
    Warning = range(5)


class Access(Enum):
    Read, \
    ReadWithWrite, \
    Write, \
    ReadWrite = range(4)


class DisplayLevel(Enum):
    Operator, \
    Expert, \
    Developer, \
    Administrator = range(4)

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

    name = None
    label = None
    description = None
    ndim = None
    format = None
    display_level = None
    display_format = None
    access = None
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

    def __init__(self):
        pass

    def isWrite(self):
        return self.access == Access.Write

    def isReadOnly(self):
        return self.access == Access.Read

    def isReadWrite(self):
        return self.access == Access.ReadWrite

    def isScalar(self):
        return self.ndim == 0

    def isSpectrum(self):
        return self.ndim == 1

    def isImage(self):
        return self.ndim == 2


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
    
    def __init__(self, r_value=None, r_timestamp=None, r_ndim=None, 
                 r_quality=None, w_value=None, exc_info=None,
                 config=None):
        self.__config= config        
        if r_timestamp is None:
            r_timestamp = datetime.datetime.now()
        self.__r_timestamp = r_timestamp     
        self.__r_value = r_value
        self.__r_ndim = r_ndim
        self.__r_quality = r_quality
        self.__w_value = w_value
        self.__exc_info = exc_info

#    def __getattr__(self, name):
#        return getattr(self.__config, name)

    def __str__(self):
        return "{0}".format(self.r_value)

    def __repr__(self):
        return "<AttributeValue({0}, {1})>".format(self.name, self.r_value)
    
    def __format__(self, format_spec):
        return '{obj.label}: {0}'.format(format(self.r_value, format_spec),
                                         obj=self)

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
    def config(self):
        return self.__config

    @config.setter
    def config(self, cfg):
        self.__config = cfg
    
    @property
    def r_value(self):
        return self.__r_value

    @property
    def value(self):
        return self.r_value

    @property
    def r_timestamp(self):
        return self.__r_timestamp

    @property
    def timestamp(self):
        return self.r_timestamp
    
    @property
    def r_ndim(self):
        return self.__r_ndim

    @property
    def ndim(self):
        return self.r_ndim

    @property
    def r_quality(self):
        return self.__r_quality

    @property
    def quality(self):
        return self.r_quality


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


class Factory(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_device(self, name):
        pass

    @abc.abstractmethod
    def get_attribute(self, name):
        pass


class Device(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self.__name = name
    
    @property
    def name(self):
        return self.__name

    @abc.abstractmethod
    def get_state(self):
        pass

    @abc.abstractmethod
    def read_attribute(self, name):
        pass

    @abc.abstractmethod
    def run_command(self, cmd, *args, **kwargs):
        pass

    def __str__(self):
        return "{0}({1})".format(self.__class__.__name__, self.__name)


class Attribute(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, device, name):
        self.__device = device
        self.__name = name

    @property
    def device(self):
        return self.__device

    @property
    def name(self):
        return self.__name

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def write(self, value):
        pass

    def __str__(self):
        return "{0}({1})".format(self.__class__.__name__, self.__name)


class Signal(object):

    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__name = kwargs.pop('name', '')
        self.__slots = []

    def __on_slot_deleted(self, slot_ref):
        self.__disconnect(slot_ref)

    def __disconnect(self, slot_ref):
        try:
            self.__slots.remove(slot_ref)
            return True
        except ValueError:
            slot = slot_ref()
            if slot is None:
                log.debug("attempting to disconnect unbound slot")
            else:
                log.debug("slot '%s' is not connected to signal",
                          slot.__name__)
        except:
            slot = slot_ref()
            if slot is None:
                log.error("Exception trying to disconnect unbound slot "
                      "from signal", exc_info='debug')
            else:
                log.error("Exception trying to disconnect slot '%s' "
                          "from signal", slot.__name__, exc_info='debug')

        return False        

    def __emit(self, slot, args, kwargs):
        try:
            slot(*args, **kwargs)
        except:
            sname = slot.__name__
            log.error("Exception emitting signal to slot '%s'",
                      sname, exc_info='debug')

    # -- API ------------------------------------------------------------------
    
    def slots(self):
        """Returns the list of connected slots"""
        slots, all_slots = [], self.__slots
        for slot in all_slots:
            slot = slot()
            if slot is not None:
                slots.append(slot)
        return slots

    def connect(self, slot):
        slot_ref = callable_weakref(slot, self.__on_slot_deleted)
        self.__slots.append(slot_ref)

    def disconnect(self, slot):
        slot_ref = callable_weakref(slot)
        self.__disconnect(slot_ref)

    def emit(self, *args, **kwargs):
        slots = self.__slots
        for slot in slots:
            self.__emit(slot(), args, kwargs)


    # -- Descriptor -----------------------------------------------------------

    def __get__(self, obj, objtype=None):
        self_ref = weakref.ref(self)
        try:
            signals = obj._qarbon_signals__
        except AttributeError:
            obj._qarbon_signals__ = signals = {}
        try:
            signal = signals[self_ref]
        except KeyError:
            signal = Signal(*self.__args, name=self.__name)
            signals[self_ref] = signal
        return signal

    def __set__(self, obj, value):
        raise AttributeError

    def __delete__(self, obj):
        try:
            del obj._qarbon_signals__[weakref(self)]
        except KeyError:
            pass
        except AttributeError:
            pass


