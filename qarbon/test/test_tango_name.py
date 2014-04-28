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

"""Test module for the :class:`~qarbon.tango.Validator` class."""

from unittest import TestCase

from qarbon.tango import Validator


class TangoNameValidatorTest(TestCase):
    """
    Test the :class:`~qarbon.tango.Validator` class
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_database(self):
        inv_db0 = "bla://host:10000"
        inv_db1 = "tango://host:bla"
        inv_db2 = "tango://111:bla"

        db0 = "tango://host:10000"
        db1 = "host:1000"
        db2 = "192.168.5.6:10000"

        Validator
