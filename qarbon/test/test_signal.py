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

from qarbon.signal import Signal

def f_slot1():
    f_slot1._called += 1
f_slot1._called = 0

def f_slot2(*args, **kwargs):
    f_slot2._args = args, kwargs
f_slot2._args = None


class UnbondSignalTest(TestCase):
    """
    Test the unbound version :class:`~qarbon.core.Signal`. 
    By unbound it means the signal is created as a standalone
    object (not bound to class)
    """

    def setUp(self):
        pass

    def tearDown(self):
        f_slot1._called = 0
        f_slot2._args = None

    def test_signal_slot_func(self):
        """Connect unbound signal to functions"""
        signal = Signal()

        # connect the signal to a slot function
        signal.connect(f_slot1)
        self.assertEquals(len(signal.slots()), 1)
        self.assertEquals(f_slot1._called, 0)

        # emit signal and check slot was called
        signal.emit()
        self.assertEquals(f_slot1._called, 1)
        # emit again signal and check slot was called
        signal.emit()
        self.assertEquals(f_slot1._called, 2)
        
        # connect again the same function
        signal.connect(f_slot1)
        self.assertEquals(len(signal.slots()), 2)
        
        # as emit on connect is True, and the signal should 
        # contain a cache, then the slot should have been called
        self.assertEquals(f_slot1._called, 3)

        # emit signal and check slot was called twice
        signal.emit()
        self.assertEquals(f_slot1._called, 5)

        # disconnect once, emit and confirm slot was called once
        signal.disconnect(f_slot1)
        self.assertEquals(len(signal.slots()), 1)

        signal.emit()
        self.assertEquals(f_slot1._called, 6)

        # disconnect last time, emit and confirm slot was not called
        signal.disconnect(f_slot1)
        self.assertEquals(len(signal.slots()), 0)

        signal.emit()
        self.assertEquals(f_slot1._called, 6)
        
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
        """Connect unbound signal to functions with args and kwargs"""
        signal = Signal()
        signal.connect(f_slot2)
        self.assertEquals(len(signal.slots()), 1)
        a1, kw1 = ("a", 1, 5.6), dict(k1=1, k2="demo", k3=True)
        signal.emit(*a1, **kw1)
        a2, kw2 = f_slot2._args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)
        
        signal.disconnect(f_slot2)
        self.assertEquals(len(signal.slots()), 0)

        # connect again to see if emit on connect was done
        f_slot2._args = None
        signal.connect(f_slot2)
        a2, kw2 = f_slot2._args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)

        signal.disconnect(f_slot2)
        self.assertEquals(len(signal.slots()), 0)

    def test_signal_slot_method(self):
        """Connect unbound signal to methods"""
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

        # as emit on connect is True, and the signal should 
        # contain a cache, then the slot should have been called
        self.assertEquals(a.slot1_count, 3)
        
        # emit signal and check slot was called twice
        signal.emit()
        self.assertEquals(a.slot1_count, 5)

        # disconnect once, emit and confirm slot was called once
        signal.disconnect(a.slot1)
        self.assertEquals(len(signal.slots()), 1)

        signal.emit()
        self.assertEquals(a.slot1_count, 6)

        # disconnect last time, emit and confirm slot was not called
        signal.disconnect(a.slot1)
        self.assertEquals(len(signal.slots()), 0)

        signal.emit()
        self.assertEquals(a.slot1_count, 6)
        
        # connect method slot to signal, delete object and check
        signal.connect(a.slot1)
        signal.connect(a.slot1)
        self.assertEquals(len(signal.slots()), 2)
        self.assertEquals(a.slot1_count, 8)
        del a
        self.assertEquals(len(signal.slots()), 0)
        
        # test emiting signal with no slots
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
        f_slot1._called = 0
        f_slot2._args = None

    def test_signal_slot_func(self):
        """Connect bound signal to a function"""        
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
        self.assertEquals(f_slot1._called, 0)

        # emit signal and check slot was called
        obj1.changeIt()
        self.assertEquals(f_slot1._called, 1)
        # emit again signal and check slot was called
        obj1.changeIt()
        self.assertEquals(f_slot1._called, 2)

        # emit on second object and confirm slot was not called
        obj2.changeIt()
        self.assertEquals(f_slot1._called, 2)
        
        # connect again the same function
        obj1.changed.connect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 2)

        # as emit on connect is True, and the signal should 
        # contain a cache, then the slot should have been called
        self.assertEquals(f_slot1._called, 3)

        # emit signal and check slot was called twice
        obj1.changeIt()
        self.assertEquals(f_slot1._called, 5)

        # disconnect once, emit and confirm slot was called once
        obj1.changed.disconnect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)

        obj1.changeIt()
        self.assertEquals(f_slot1._called, 6)

        # disconnect last time, emit and confirm slot was not called
        obj1.changed.disconnect(f_slot1)
        self.assertEquals(len(obj1.changed.slots()), 0)

        obj1.changeIt()
        self.assertEquals(f_slot1._called, 6)
        
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
        """Connect bound signal to a function with args and kwargs"""       
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
        a2, kw2 = f_slot2._args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)
        
        obj1.changed.disconnect(f_slot2)
        self.assertEquals(len(obj1.changed.slots()), 0)

        # connect again to see if emit on connect was done
        f_slot2._args = None
        obj1.changed.connect(f_slot2)
        a2, kw2 = f_slot2._args
        self.assertEquals(a1, a2)
        self.assertEquals(kw1, kw2)
        
        obj1.changed.disconnect(f_slot2)
        self.assertEquals(len(obj1.changed.slots()), 0)

    def test_signal_slot_method(self):
        """Connect bound signal to a method"""
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

        # as emit on connect is True, and the signal should 
        # contain a cache, then the slot should have been called
        self.assertEquals(a.slot1_count, 3)
        
        # emit signal and check slot was called twice
        obj1.changeIt()
        self.assertEquals(a.slot1_count, 5)

        # disconnect once, emit and confirm slot was called once
        obj1.changed.disconnect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 1)

        obj1.changeIt()
        self.assertEquals(a.slot1_count, 6)

        # disconnect last time, emit and confirm slot was not called
        obj1.changed.disconnect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 0)

        obj1.changeIt()
        self.assertEquals(a.slot1_count, 6)
        
        # connect method slot to signal, delete object and check
        obj1.changed.connect(a.slot1)
        obj1.changed.connect(a.slot1)
        self.assertEquals(len(obj1.changed.slots()), 2)

        self.assertEquals(a.slot1_count, 8)
        del a
        self.assertEquals(len(obj1.changed.slots()), 0)

        # test emiting signal with no slots
        obj1.changeIt()
