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
           "State", "Manager", "IScheme", "IDatabase", "IDevice", "IAttribute",
           "Scheme", "Database", "Device", "Attribute"]

import os
import re
import abc
import imp
import sys
import inspect
import collections

from qarbon.external.enum import Enum

from qarbon import config
from qarbon.node import Node
from qarbon.signal import Signal
from qarbon.util import is_string

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
        if isString(dtype):
            dtype = dtype.lower()
        return DataType.__DTYPE_MAP[dtype]


class State(Enum):
    """State enum."""
    # On, Moving, Fault, Alarm, Unknown, _Invalid = range(6)

    On, Off, Close, Open, Insert, Extract, Moving, Standby, Fault, Init, \
    Running, Alarm, Disable, Unknown, Disconnected, _Invalid = range(16)


QARBON_PLUGIN_MAGIC = "__qarbon_plugin__"


def get_plugin_candidates():
    """Get candidate plugin directories"""
    plugins = []
    for path in config.PLUGIN_PATH:
        for elem in os.listdir(path):
            if elem.startswith(".") or elem.startswith("."):
                continue
            full_elem = os.path.join(path, elem)
            if not os.path.isdir(full_elem):
                continue
            if not os.path.exists(os.path.join(full_elem, "__init__.py")):
                continue
            plugins.append((path, elem))
    return plugins


def get_plugins():
    plugins = []
    plugin_candidates = get_plugin_candidates()
    for path, plugin in plugin_candidates:
        try:
            plugin_info = imp.find_module(plugin, [path])
        except ImportError:
            continue
        plugin_module = imp.load_module(plugin, *plugin_info)
        if hasattr(plugin_module, QARBON_PLUGIN_MAGIC):
            plugins.append(plugin_module)
        for member_name, member in inspect.getmembers(plugin_module):
            if inspect.isclass(member) and hasattr(member, QARBON_PLUGIN_MAGIC):
                plugins.append(member)
    return plugins


def get_control_plugins():
    plugins = []
    for plugin in get_plugins():
        magic = getattr(plugin, QARBON_PLUGIN_MAGIC)
        if isinstance(magic, collections.Mapping):
            ptype = magic.get("type")
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
    return __MANAGER


class IScheme(Node):
    __metaclass__ = abc.ABCMeta

    """
    Base scheme class.
    """

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
    __metaclass__ = abc.ABCMeta

    """
    Base database class
    """

    def __init__(self, name, parent=None):
        Node.__init__(self, name, parent=parent)

    @abc.abstractmethod
    def get_device(self, object_name):
        pass


class IDevice(Node):
    __metaclass__ = abc.ABCMeta

    """
    Base device class.
    """

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
    __metaclass__ = abc.ABCMeta

    """
    Base attribute class.
    """

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
    return Manager().get_database(name)


def Device(name):
    return Manager().get_device(name)


def Attribute(name):
    return Manager().get_attribute(name)
