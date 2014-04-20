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

"""Simple implementation of signal/slot pattern."""

__all__ = ["Signal"]

import weakref

from . import log
from .util import callable_weakref


class Signal(object):
    
    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__name = kwargs.pop('name', '')
        self.__emit_on_connect = kwargs.pop('emit_on_connect', True)
        self.__slots = []
        self.__cache = None

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

    # -- Descriptor API -------------------------------------------------------

    def __get__(self, obj, objtype=None):
        self_ref = weakref.ref(self)
        try:
            signals = obj._qarbon_signals__
        except AttributeError:
            obj._qarbon_signals__ = signals = {}
        try:
            signal = signals[self_ref]
        except KeyError:
            signal = Signal(*self.__args, name=self.__name,
                             emit_on_connect=self.__emit_on_connect)
            signals[self_ref] = signal
        return signal

    def __set__(self, obj, value):
        raise AttributeError

    def __delete__(self, obj):
        try:
            del obj._qarbon_signals__[weakref.ref(self)]
        except KeyError:
            pass
        except AttributeError:
            pass

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
        if self.__emit_on_connect and self.__cache is not None:
            self.__emit(slot, *self.__cache)

    def disconnect(self, slot):
        slot_ref = callable_weakref(slot)
        self.__disconnect(slot_ref)

    def emit(self, *args, **kwargs):
        self.__cache = args, kwargs
        slots = self.__slots
        for slot in slots:
            self.__emit(slot(), args, kwargs)

