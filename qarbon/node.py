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

"""Node module."""

__all__ = ["Node"]

import weakref


class Node(object):
    """
    Node class representing a node in a tree.
    
    A strong reference is kept on the parent node.
    Weak references are kept on the childs.
    """

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
    def __repr__(self):
        cname, name = self.__class__.__name__, self.__name
        return "{0}(name={1})".format(cname, name)

    def __str__(self):
        cname, name = self.__class__.__name__, self.__name
        return "{0}({1})".format(cname, name)

    # -- more complete repr and str -------------------------------------------
#    def __repr__(self):
#       cname, parent, name = self.__class__.__name__, self.__parent, self.__name
#       if parent is None:
#           return "{0}(name={1})".format(cname, name)
#       return "{0}(name={1}, parent={2!r})".format(cname, name, parent)
 
#    def __str__(self):
#       cname, parent, name = self.__class__.__name__, self.__parent, self.__name
#       if parent is None:
#           return "{0}({1})".format(cname, name)
#       return "{0}({1}, {2})".format(cname, name, parent)
