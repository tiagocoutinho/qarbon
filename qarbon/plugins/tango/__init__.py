# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Qarbon's tango plugin."""

__all__ = ["Scheme", "Database", "Device", "Attribute", "Object"]

__qarbon_plugin__ = {
    "type": "Control",
}

schemes = "tango",

def Scheme():
    from .tango import Scheme as S
    return S()

def Database(name):
    return Scheme().get_database(name)

def Device(name):
    return Scheme().get_device(name)

def Attribute(name):
    return Scheme().get_attribute(name)

def Object(name):
    return Scheme().get_object(name)

