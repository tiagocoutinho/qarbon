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

"""Plugin extension manager."""

__all__ = ["get_plugins", "get_plugin_info", "IPlugin"]

import os
import abc
import imp
import inspect
import functools

from qarbon import config

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


def get_plugin_info(plugin):
    return getattr(plugin, QARBON_PLUGIN_MAGIC)


def IPlugin(klass=None, **kwargs):
    """
    Decorator that transforms the decorated class into a plugin point.
    """
    if klass is None:
        return functools.partial(IPlugin, **kwargs)
    setattr(klass, QARBON_PLUGIN_MAGIC, kwargs)
    return klass
