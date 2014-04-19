# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Helper functions."""

__all__ = ['isString', 'isSequence', 'moduleImport', 'moduleDirectory',
           'callable_weakref']

import os
import sys
import inspect
import weakref
import collections


__str_klasses = [str]
__seq_klasses = [collections.Sequence, bytearray]

# some versions of python don't have unicode (python [3.0, 3.3])
try:
    unicode
    __str_klasses.append(unicode)
except:
    pass

# some versions of python don't have basestring (python [3.0, inf[)
try:
    basestring
    __str_klasses.insert(0, basestring)
except:
    pass

__str_klasses = tuple(__str_klasses)
__seq_klasses = tuple(__seq_klasses)


def isString(obj):
    """Determines if the given object is a string.

    :param obj: the object to be analysed
    :type obj: object
    :return: True if the given object is a string or False otherwise
    :rtype: bool"""
    return isinstance(obj, __str_klasses)


def isSequence(obj, inc_string=False):
    """Determines if the given object is a sequence.

    :param obj: the object to be analysed
    :type obj: object
    :param inc_string: if False, exclude str/unicode objects from the list
                       of possible sequence objects
    :type inc_string: bool
    :return: True if the given object is a sequence or False otherwise
    :rtype: bool"""
    if inc_string:
        return isinstance(obj, __seq_klasses)
    else:
        return isinstance(obj, __seq_klasses) and not isString(obj)


def moduleImport(name):
    """Import module, returning the module after the last dot.

    :param name: name of the module to be imported
    :type name: str
    :return: the imported module
    :rtype: module"""
    __import__(name)
    return sys.modules[name]


def moduleDirectory(module):
    """Returns the location of a given module.

    :param module: the module object
    :type module: module
    :return: the directory where the module is located
    :rtype: str"""
    return os.path.dirname(os.path.abspath(module.__file__))


class _MethodWeakref(object):
    """This class represents a weak reference to a method of an object since
    weak references to methods don't work by themselves"""
    
    def __init__(self, method, del_cb=None):
        cb = del_cb and self.__on_deleted
        self.__func = weakref.ref(method.im_func, cb) 
        self.__obj = weakref.ref(method.im_self, cb)
        if cb:
            self.__del_cb = callable_weakref(del_cb)
        self.__deleted = 0

    def __on_deleted(self, obj):
        if not self.__deleted:
            del_cb = self.__del_cb()
            if del_cb is not None:
                del_cb(self)
                self.__deleted = 1
        
    def __call__(self):
        obj = self.__obj()
        if obj is not None:
            func = self.__func()
            if func is not None:
                return func.__get__(obj)

    def __hash__(self):
        return id(self)

    def __cmp__(self, other):
        if other.__class__ == self.__class__:
            ret = cmp((self.__func, self.__obj),
                      (other.__func, other.__obj))
            return ret
        return 1

    def __repr__(self):
        return '_MethodWeakRef()'
        #obj, f_name = self.__obj(), self.__func().__name__
        #return '_MethodWeakRef(obj={0}, func={1})'.format % (obj, f_name)


def callable_weakref(obj, del_cb=None):
    """This function returns a callable weak reference to a callable object. 
    Object can be a callable object, a function or a method.
    
    :param object: a callable object
    :type object: callable object
    :param del_cb: calback function. Default is None meaning to callback.
    :type del_cb: callable object or None
    
    :return: a weak reference for the given callable
    :rtype: BoundMethodWeakref or weakref.ref"""
    if inspect.ismethod(obj):
        return _MethodWeakref(obj, del_cb)
    return weakref.ref(obj, del_cb)
