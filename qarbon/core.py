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

__all__ = ["Quality", "Access", "DisplayLevel", "DataType", "State", 
           "Manager", "IScheme", "IDatabase", "IDevice", "IAttribute",
           "Database", "Device", "Attribute"]

import os
import re
import abc
import sys
import collections

from qarbon.external.enum import Enum

from qarbon import config
from qarbon.node import Node
from qarbon.signal import Signal
from qarbon.util import is_string
from qarbon.plugin import get_plugins, get_plugin_info

_PY3 = sys.version_info[0] > 2

ErrorStr = ErrorRepr = "Error!"


class Quality(Enum):
    """Quality enum."""
    Valid, \
    Invalid, \
    Alarm, \
    Changing, \
    Warning, \
    _Invalid = range(6)


class Access(Enum):
    """Access enum."""
    Read, \
    ReadWithWrite, \
    Write, \
    ReadWrite, \
    _Invalid = range(5)


class DisplayLevel(Enum):
    """Display level enum."""
    Operator, \
    Expert, \
    Developer, \
    Administrator, \
    _Invalid = range(5)


class DataType(Enum):
    """Data type enum."""

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
    def to_python_type(dtype):
        """Convert from DataType to python type"""
        dtype = DataType.to_data_type(dtype)
        return DataType.__PYTYPE_MAP[dtype]

    @staticmethod
    def to_data_type(dtype):
        """Convert from type to DataType"""
        if is_string(dtype):
            dtype = dtype.lower()
        return DataType.__DTYPE_MAP[dtype]


class State(Enum):
    """State enum."""
    # On, Moving, Fault, Alarm, Unknown, _Invalid = range(6)

    On, Off, Close, Open, Insert, Extract, Moving, Standby, Fault, Init, \
    Running, Alarm, Disable, Unknown, Disconnected, _Invalid = range(16)


def get_control_plugins():
    """Returns the list of control plugins."""
    plugins = []
    for plugin in get_plugins():
        info = get_plugin_info(plugin)
        if isinstance(info, collections.Mapping):
            ptype = info.get("type")
            if ptype == "Control":
                plugins.append(plugin)
    return plugins


class _Manager(object):

    _SchemeRE = re.compile('^(?P<scheme>[\w\-]+)://(?P<trail>.*)')

    def __init__(self):
        self.__plugin_cache = None

    def get_device(self, name):
        match = self._SchemeRE.match(name)
        scheme = config.DEFAULT_SCHEME
        if match:
            scheme = match.group("scheme")
        plugin = self.get_plugin(scheme)
        return plugin.Device(name)

    def __get_plugins(self):
        plugins = self.__plugin_cache
        if plugins is None:
            plugins = {}
            for plugin in get_control_plugins():
                for scheme in plugin.schemes:
                    if scheme in plugins:
                        log.error("Conflicting plugins for scheme %s", scheme)
                        continue
                    plugins[scheme] = plugin
            self.__plugin_cache = plugins
        return plugins

    def reload_plugins(self):
        self.__plugin_cache = None
        return self.__get_plugins()

    def get_plugin(self, scheme):
        try:
            return self.__get_plugins()[scheme]
        except KeyError:
            raise KeyError("Unknown plugin '{0}'".format(scheme))
    def register_plugin(self):
        pass


__MANAGER = _Manager()
def Manager():
    """Returns the one and only core Manager."""
    return __MANAGER


class IScheme(Node):
    """
    Base scheme class.

    Plugins should provide an implementation of this class.
    """

    __metaclass__ = abc.ABCMeta

    schemes = ()

    def __init__(self, name=None, parent=None):
        if name is None:
            name = self.__class__.__name__
        Node.__init__(self, name, parent=parent)

    @abc.abstractmethod
    def get_database(self, name):
        pass

    @abc.abstractmethod
    def get_device(self, name):
        pass

    @abc.abstractmethod
    def get_attribute(self, name):
        pass


class IDatabase(Node):
    """
    Base database class.

    Plugins should provide an implementation of this class
    as a response to a get_database from their Scheme
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, parent=None):
        Node.__init__(self, name, parent=parent)

    @abc.abstractmethod
    def get_device(self, object_name):
        pass


class IDevice(Node):
    """
    Base device class.

    Plugins should provide an implementation of this class
    as a response to a get_device from their Scheme
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, parent=None):
        Node.__init__(self, name, parent=parent)

    @property
    def database(self):
        return self.get_parent()

    @abc.abstractmethod
    def get_attribute(self, attr_name):
        pass

    @abc.abstractmethod
    def execute(self, cmd, *args, **kwargs):
        pass


class IAttribute(Node):
    """
    Base attribute class.

    Plugins should provide an implementation of this class
    as a response to a get_attribute from their Scheme
    """

    __metaclass__ = abc.ABCMeta

    #: Signal emited when the attribute value changes
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        Node.__init__(self, name, parent=parent)

    @property
    def device(self):
        return self.get_parent()

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def write(self, value):
        pass


def Database(name=None):
    """Helper to get the database corresponding to the given name."""
    return Manager().get_database(name)


def Device(name):
    """Helper to get the device corresponding to the given name."""
    return Manager().get_device(name)


def Attribute(name):
    """Helper to get the attribute corresponding to the given name."""
    return Manager().get_attribute(name)
