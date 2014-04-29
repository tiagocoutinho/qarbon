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


def __get_plugin_candidates():
    """
    Gets the list of candidate plugin directories.

    A directory is considered to be a candidate for a plugin if
    it is inside a directory in the PLUGIN_PATH and it contains
    at least an *__init__.py* file.

    Returns a sequence of tuples with two elements:
    - the directory where the plugin resides
    - the plugin name (= directory name)

    :return: sequence of tuple<path(str), name(str)>
    """
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
    """
    Gets the list of reachable plugins.

    Returns a sequence of python objects that are plugins.
    
    A python object is a valid plugin ig it contains a member
    called *__qarbon_plugin__*. It can be a python module or
    a python class.

    :return: sequence of python objects that are plugins
    """
    plugins = []
    plugin_candidates = __get_plugin_candidates()
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
    """
    Gets the plugin meta information.
    
    Basically is just the dictionary that the __qarbon_plugin__ member of the
    given plugin points to.

    :return: a map of the plugin meta information.
    """
    return getattr(plugin, QARBON_PLUGIN_MAGIC)


def IPlugin(klass=None, **kwargs):
    """
    Decorator that transforms the decorated class into a plugin point.
    Example::
    
        from qarbon.plugin import IPlugin

        @IPlugin
        class SendMailPlugin(object):

            def send_mail(self, recipients, title, content):
                pass

        @IPlugin(name="bla", mode="expert")
        class SuperPlugin(object):
            
            def i_do_super_stuff(self):
                pass

    """
    if klass is None:
        return functools.partial(IPlugin, **kwargs)
    setattr(klass, QARBON_PLUGIN_MAGIC, kwargs)
    return klass
