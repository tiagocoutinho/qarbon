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

"""Test module for the :class:`~qarbon.core.Signal` class."""

from unittest import TestCase

from qarbon.core import Signal

_f_slot1_called = 0
def f_slot1():
    global _f_slot1_called
    _f_slot1_called += 1

_f_slot2_args = None
def f_slot2(*args, **kwargs):
    global _f_slot2_args
    _f_slot2_args = args, kwargs


class UnbondSignalTest(TestCase):
    """
    Test the unbound version :class:`~qarbon.core.Signal`. 
    By unbound it means the signal is created as a standalone
    object (not bound to class)
    """

    def setUp(self):
        pass

    def tearDown(self):
        global _f_slot1_called
        global _f_slot2_args
        _f_slot1_called = 0
        _f_slot2_args = None

    def test_signal_slot_func(self):
        """Tests connecting unbound signal to a function"""
        signal = Signal()

        # connect the signal to a slot function
        signal.connect(f_slot1)
        self.assertEquals(len(signal.slots()), 1)
        self.assertEquals(_f_slot1_called, 0)

        # emit signal and check slot was called
        signal.emit()
        self.assertEquals(_f_slot1_called, 1)
        # emit again signal and check slot was called
        signal.emit()
        self.assertEquals(_f_slot1_called, 2)
        
        # connect again the same function
        signal.connect(f_slot1)
        self.assertEquals(len(signal.slots()), 2)
        
        # emit signal and check slot was called twice
        signal.emit()
        self.assertEquals(_f_slot1_called, 4)

        # disconnect once, emit and confirm slot was called once
        signal.disconnect(f_slot1)
        self.assertEquals(len(signal.slots()), 1)

        signal.emit()
        self.assertEquals(_f_slot1_called, 5)

        # disconnect last time, emit and confirm slot was not called
        signal.disconnect(f_slot1)
        self.assertEquals(len(signal.slots()), 0)

        signal.emit()
        self.assertEquals(_f_slot1_called, 5)
        
        # temporary slot
        self._temp_called = False
        def temp_func():
            self._temp_called = True
        
        signal.connect(temp_func)
        self.assertEquals(len(signal.slots()), 1)
        signal.emit()
        self.assert_(self._temp_called)

        # delete temporary slot and confirm slot is no longer in signal
        del temp_func
        self.assertEquals(len(signal.slots()), 0)

    def test_signal_slot_func_args(self):
        """Tests connecting unbound signal to a function with args and kwargs"""
        signal = Signal()
        signal.connect(f_slot2)
        self.assertEquals(len(signal.slots()), 1)
        a1, kw1 = ("a", 1, 5.6), dict(k1=1, k2="demo", k3=True)
        signal.emit(*a1, **kw1)
        a2, kw2 = _f_slot2_args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)
        
        signal.disconnect(f_slot2)
        self.assertEquals(len(signal.slots()), 0)

    def test_signal_slot_method(self):
        """Tests connecting unbound signal to a method"""
        signal = Signal()

        class A(object):
            def __init__(self):
                self.slot1_count = 0
            def slot1(self):
                self.slot1_count += 1
        
        a = A()

        # connect the signal to a slot function
        signal.connect(a.slot1)
        self.assertEquals(len(signal.slots()), 1)
        self.assertEquals(a.slot1_count, 0)

        # emit signal and check slot was called
        signal.emit()
        self.assertEquals(a.slot1_count, 1)
        # emit again signal and check slot was called
        signal.emit()
        self.assertEquals(a.slot1_count, 2)
        
        # connect again the same function
        signal.connect(a.slot1)
        self.assertEquals(len(signal.slots()), 2)
        
        # emit signal and check slot was called twice
        signal.emit()
        self.assertEquals(a.slot1_count, 4)

        # disconnect once, emit and confirm slot was called once
        signal.disconnect(a.slot1)
        self.assertEquals(len(signal.slots()), 1)

        signal.emit()
        self.assertEquals(a.slot1_count, 5)

        # disconnect last time, emit and confirm slot was not called
        signal.disconnect(a.slot1)
        self.assertEquals(len(signal.slots()), 0)

        signal.emit()
        self.assertEquals(a.slot1_count, 5)
        
        # connect method slot to signal, delete object and check
        signal.connect(a.slot1)
        signal.connect(a.slot1)
        self.assertEquals(len(signal.slots()), 2)
        signal.emit()
        self.assertEquals(a.slot1_count, 7)
        del a
        self.assertEquals(len(signal.slots()), 0)
        signal.emit()


class BondSignalTest(TestCase):
    """
    Test the bound version :class:`~qarbon.core.Signal`. 
    By bound it means the signal is created as a member of
    a class (it is bound to that class)
    """

    def setUp(self):
        pass

    def tearDown(self):
        global _f_slot1_called
        global _f_slot2_args
        _f_slot1_called = 0
        _f_slot2_args = None

    def test_signal_slot_func(self):
        """Tests connecting bound signal to a function"""        
        class Object(object):
            changed = Signal()

            def changeIt(self, *args, **kwargs):
                self.changed.emit(*args, **kwargs)

        obj1 = Object()
        obj2 = Object()

        # connect the signal to a slot function
        obj1.changed.connect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)
        self.assertEquals(len(obj2.changed.slots()), 0)
        self.assertEquals(_f_slot1_called, 0)

        # emit signal and check slot was called
        obj1.changeIt()
        self.assertEquals(_f_slot1_called, 1)
        # emit again signal and check slot was called
        obj1.changeIt()
        self.assertEquals(_f_slot1_called, 2)

        # emit on second object and confirm slot was not called
        obj2.changeIt()
        self.assertEquals(_f_slot1_called, 2)
        
        # connect again the same function
        obj1.changed.connect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 2)
        
        # emit signal and check slot was called twice
        obj1.changeIt()
        self.assertEquals(_f_slot1_called, 4)

        # disconnect once, emit and confirm slot was called once
        obj1.changed.disconnect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)

        obj1.changeIt()
        self.assertEquals(_f_slot1_called, 5)

        # disconnect last time, emit and confirm slot was not called
        obj1.changed.disconnect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 0)

        obj1.changeIt()
        self.assertEquals(_f_slot1_called, 5)
        
        # temporary slot
        self._temp_called = False
        def temp_func():
            self._temp_called = True
        
        obj1.changed.connect(temp_func)
        self.assertEquals(len(obj1.changed.slots()), 1)
        obj1.changeIt()
        self.assert_(self._temp_called)

        # delete temporary slot and confirm slot is no longer in signal
        del temp_func
        self.assertEquals(len(obj1.changed.slots()), 0)

    def test_signal_slot_func_args(self):
        """Tests connecting bound signal to a function with args and kwargs"""       
        class Object(object):
            changed = Signal()

            def changeIt(self, *args, **kwargs):
                self.changed.emit(*args, **kwargs)

        obj1 = Object()
        obj2 = Object()

        obj1.changed.connect(f_slot2)
        self.assertEquals(len(obj1.changed.slots()), 1)
        self.assertEquals(len(obj2.changed.slots()), 0)
        a1, kw1 = ("a", 1, True), dict(k1=1, k2="demo", k3=4.5, k4="bla")
        obj1.changeIt(*a1, **kw1)
        a2, kw2 = _f_slot2_args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)
        
        obj1.changed.disconnect(f_slot2)
        self.assertEquals(len(obj1.changed.slots()), 0)

    def test_signal_slot_method(self):
        """Tests connecting bound signal to a method"""
        class Object(object):
            changed = Signal()

            def changeIt(self, *args, **kwargs):
                self.changed.emit(*args, **kwargs)

        obj1 = Object()
        obj2 = Object()

        class A(object):
            def __init__(self):
                self.slot1_count = 0
            def slot1(self):
                self.slot1_count += 1
        
        a = A()

        # connect the signal to a slot function
        obj1.changed.connect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)
        self.assertEquals(len(obj2.changed.slots()), 0)
        self.assertEquals(a.slot1_count, 0)

        # emit signal and check slot was called
        obj1.changeIt()
        self.assertEquals(a.slot1_count, 1)
        # emit again signal and check slot was called
        obj1.changeIt()
        self.assertEquals(a.slot1_count, 2)
        
        # connect again the same function
        obj1.changed.connect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 2)
        
        # emit signal and check slot was called twice
        obj1.changeIt()
        self.assertEquals(a.slot1_count, 4)

        # disconnect once, emit and confirm slot was called once
        obj1.changed.disconnect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)

        obj1.changeIt()
        self.assertEquals(a.slot1_count, 5)

        # disconnect last time, emit and confirm slot was not called
        obj1.changed.disconnect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 0)

        obj1.changeIt()
        self.assertEquals(a.slot1_count, 5)
        
        # connect method slot to signal, delete object and check
        obj1.changed.connect(a.slot1)
        obj1.changed.connect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 2)
        obj1.changeIt()
        self.assertEquals(a.slot1_count, 7)
        del a
        self.assertEquals(len(obj1.changed.slots()), 0)
        obj1.changeIt()
